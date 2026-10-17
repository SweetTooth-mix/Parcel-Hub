"""Opt-in Telegram linking and durable delivery. Run: python -m app.telegram.

Only this worker contacts Telegram. Web requests commit an outbox entry, so a
Telegram outage cannot roll back a parcel transaction. Pickup OTPs are resolved
only at delivery, while valid, for the linked recipient.
"""

import json
import logging
import re
import sqlite3
from fastapi import HTTPException
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import Settings
from .database import initialize, transaction
from .security import fingerprint, token
from . import service as svc
from . import bot_orders

LOG = logging.getLogger("parcelhub.telegram")
LINK_SECONDS = 600
MESSAGE_SECONDS = 86400


class TelegramError(Exception):
    def __init__(self, code=0, retry_after=0):
        self.code = code if isinstance(code, int) else 0
        self.retry_after = retry_after if isinstance(retry_after, int) else 0
        # Never expose Telegram's request URL (which contains the bot token).
        super().__init__(f"Telegram API error ({self.code})")


class TelegramClient:
    def __init__(self, bot_token):
        self._token = bot_token

    def call(self, method, **params):
        request = Request(
            f"https://api.telegram.org/bot{self._token}/{method}",
            data=json.dumps(params).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=20) as response:
                payload = json.loads(response.read(1048576))
        except HTTPError as error:
            try:
                payload = json.loads(error.read(65536))
            except (ValueError, OSError):
                payload = {}
            parameters = (
                payload.get("parameters") if isinstance(payload, dict) else None
            )
            raise TelegramError(
                error.code,
                parameters.get("retry_after", 0) if isinstance(parameters, dict) else 0,
            ) from None
        except (URLError, OSError, ValueError):
            raise TelegramError() from None
        if not isinstance(payload, dict) or not payload.get("ok"):
            parameters = (
                payload.get("parameters") if isinstance(payload, dict) else None
            )
            raise TelegramError(
                payload.get("error_code", 0) if isinstance(payload, dict) else 0,
                parameters.get("retry_after", 0) if isinstance(parameters, dict) else 0,
            )
        return payload.get("result")


def setting(db, name, default="0"):
    row = db.execute(
        "SELECT value FROM settings WHERE key=?", ("telegram_" + name,)
    ).fetchone()
    return row["value"] if row else default


def put_setting(db, name, value):
    db.execute(
        "INSERT INTO settings(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        ("telegram_" + name, str(value)),
    )


def status(db, uid, cfg):
    account = db.execute(
        "SELECT * FROM telegram_accounts WHERE user_id=?", (uid,)
    ).fetchone()
    delivery = db.execute(
        """SELECT SUM(status IN ('pending','sending')) pending,
           SUM(status='failed') failed, MAX(sent_at) last_sent_at
           FROM telegram_outbox WHERE user_id=? AND connection_id=?""",
        (uid, account["connection_id"] if account else ""),
    ).fetchone()
    return {
        "enabled": cfg.telegram_enabled,
        "ready": cfg.telegram_enabled
        and int(setting(db, "heartbeat")) > int(time.time()) - 90,
        "connected": bool(account),
        "display_name": account["display_name"] if account else None,
        "connected_at": account["connected_at"] if account else None,
        "pending": delivery["pending"] or 0,
        "failed": delivery["failed"] or 0,
        "last_sent_at": delivery["last_sent_at"],
    }


def create_link(db, uid, cfg):
    svc.require(cfg.telegram_enabled, "Telegram belum diaktifkan oleh pentadbir.", 503)
    svc.require(
        status(db, uid, cfg)["ready"],
        "Bot Telegram belum tersedia. Cuba sebentar lagi.",
        503,
    )
    svc.require(
        not db.execute(
            "SELECT 1 FROM telegram_accounts WHERE user_id=?", (uid,)
        ).fetchone(),
        "Putuskan sambungan sedia ada dahulu.",
    )
    raw = token()
    expires = int(time.time()) + LINK_SECONDS
    db.execute(
        "DELETE FROM telegram_links WHERE user_id=? OR expires_at<=?",
        (uid, int(time.time())),
    )
    db.execute(
        "INSERT INTO telegram_links VALUES (?,?,?)",
        (fingerprint(raw, cfg.secret), uid, expires),
    )
    return {
        "url": f"https://t.me/{cfg.telegram_bot_username}?start={raw}",
        "expires_at": expires,
    }


def disconnect(db, uid):
    db.execute("DELETE FROM telegram_accounts WHERE user_id=?", (uid,))
    db.execute("DELETE FROM telegram_links WHERE user_id=?", (uid,))
    db.execute("DELETE FROM telegram_drafts WHERE user_id=?", (uid,))
    db.execute(
        "UPDATE telegram_outbox SET status='cancelled' WHERE user_id=? AND status IN ('pending','sending')",
        (uid,),
    )


def process_update(cfg, update):
    """Accept authenticated Bot API updates, never arbitrary browser callbacks."""
    now = int(time.time())
    with transaction(cfg) as db:
        update_id = update.get("update_id")
        if not isinstance(update_id, int) or update_id < int(setting(db, "offset")):
            return None
        put_setting(db, "offset", update_id + 1)
        member = update.get("my_chat_member", {})
        if (
            member.get("chat", {}).get("type") == "private"
            and member.get("new_chat_member", {}).get("status") == "kicked"
        ):
            account = db.execute(
                "SELECT user_id FROM telegram_accounts WHERE chat_id=?",
                (member["chat"]["id"],),
            ).fetchone()
            if account:
                disconnect(db, account["user_id"])
            return None
        message = update.get("message", {})
        chat = message.get("chat", {})
        sender = message.get("from", {})
        chat_id = chat.get("id")
        if (
            chat.get("type") != "private"
            or not isinstance(chat_id, int)
            or chat_id <= 0
            or sender.get("id") != chat_id
            or sender.get("is_bot")
        ):
            return None
        text = message.get("text", "")
        if not isinstance(text, str) or len(text) > 4096:
            return None
        text = text.strip()
        if text.split(" ", 1)[0].split("@")[0] == "/stop":
            account = db.execute(
                "SELECT user_id FROM telegram_accounts WHERE chat_id=?", (chat_id,)
            ).fetchone()
            if account:
                disconnect(db, account["user_id"])
                svc.audit(db, account["user_id"], "TELEGRAM_DISCONNECTED")
            return (
                chat_id,
                "Notifikasi Telegram dihentikan. Notifikasi dalam portal ParcelHub masih tersedia.",
            )
        match = re.fullmatch(r"/start(?:@[A-Za-z0-9_]+)? ([A-Za-z0-9_-]{43})", text)
        if not match:
            account = db.execute(
                "SELECT u.* FROM users u JOIN telegram_accounts a ON a.user_id=u.id WHERE a.chat_id=?",
                (chat_id,),
            ).fetchone()
            if not account:
                return (
                    chat_id,
                    "Daftar/log masuk di ParcelHub → Akaun & sistem → Sambung Telegram. Tekan Start pada pautan itu untuk membuat order dan menerima kod pengambilan.",
                )
            db.execute("SAVEPOINT bot_action")
            try:
                reply, options = bot_orders.handle(db, dict(account), text, cfg)
            except (HTTPException, sqlite3.IntegrityError) as error:
                db.execute("ROLLBACK TO bot_action")
                reply = (
                    error.detail
                    if isinstance(error, HTTPException)
                    else "Rekod sudah diproses. Semak order sebelum mencuba lagi."
                )
                options = {}  # retain the keyboard for the current wizard step
            finally:
                db.execute("RELEASE bot_action")
            return chat_id, reply, options
        link = db.execute(
            "SELECT * FROM telegram_links WHERE token_hash=? AND expires_at>?",
            (fingerprint(match[1], cfg.secret), now),
        ).fetchone()
        if not link:
            return (
                chat_id,
                "Pautan tidak sah atau tamat tempoh. Jana pautan baharu dalam tetapan ParcelHub.",
            )
        if db.execute(
            "SELECT 1 FROM telegram_accounts WHERE user_id=? OR chat_id=?",
            (link["user_id"], chat_id),
        ).fetchone():
            return (
                chat_id,
                "Akaun ini sudah mempunyai sambungan. Putuskan sambungan lama dalam ParcelHub atau hantar /stop dahulu.",
            )
        name = (
            "@" + sender["username"]
            if sender.get("username")
            else sender.get("first_name", "Akaun Telegram")
        )[:80]
        db.execute(
            "INSERT INTO telegram_accounts VALUES (?,?,?,?,?)",
            (link["user_id"], chat_id, name, token(), now),
        )
        db.execute("DELETE FROM telegram_links WHERE user_id=?", (link["user_id"],))
        svc.audit(db, link["user_id"], "TELEGRAM_CONNECTED")
        return (
            chat_id,
            "Telegram disambungkan. Order, notifikasi dan kod pengambilan boleh diurus di sini. Tekan /help untuk menu. Hantar /stop untuk berhenti.",
            bot_orders.menu(
                dict(
                    db.execute(
                        "SELECT * FROM users WHERE id=?", (link["user_id"],)
                    ).fetchone()
                )
            ),
        )


def deliver_one(cfg, client, now=None):
    now = int(time.time()) if now is None else now
    with transaction(cfg) as db:
        if int(setting(db, "retry_at")) > now:
            return False
        db.execute(
            """UPDATE telegram_outbox SET status='cancelled'
               WHERE status IN ('pending','sending') AND
               (created_at<=? OR NOT EXISTS (SELECT 1 FROM telegram_accounts a
                WHERE a.user_id=telegram_outbox.user_id AND a.connection_id=telegram_outbox.connection_id))""",
            (now - MESSAGE_SECONDS,),
        )
        row = db.execute(
            """SELECT o.* FROM telegram_outbox o JOIN telegram_accounts a ON a.connection_id=o.connection_id
               WHERE o.next_attempt_at<=? AND (o.status='pending' OR (o.status='sending' AND o.lease_until<=?))
               AND NOT EXISTS (SELECT 1 FROM telegram_outbox recent WHERE recent.chat_id=o.chat_id AND recent.sent_at>=?)
               ORDER BY o.id LIMIT 1""",
            (now, now, now),
        ).fetchone()
        if not row:
            return False
        row = dict(row)
        text, stale = svc.notification_text(
            db, row["notification_id"], row["text"], cfg
        )
        if stale:
            db.execute(
                "UPDATE telegram_outbox SET status='cancelled',last_error='code_no_longer_valid' WHERE id=?",
                (row["id"],),
            )
            return True
        db.execute(
            "UPDATE telegram_outbox SET status='sending',attempts=attempts+1,lease_until=? WHERE id=?",
            (now + 60, row["id"]),
        )
    text = text[:3500]
    if cfg.origin.startswith("https://"):
        text += f"\n\nPortal: {cfg.origin}/#notifications"
    try:
        result = client.call(
            "sendMessage",
            chat_id=row["chat_id"],
            text=text,
            link_preview_options={"is_disabled": True},
        )
    except TelegramError as error:
        with transaction(cfg) as db:
            if error.code == 403:
                # Do not disconnect a newer connection if this request was in flight.
                current = db.execute(
                    "SELECT user_id FROM telegram_accounts WHERE connection_id=?",
                    (row["connection_id"],),
                ).fetchone()
                if current:
                    disconnect(db, current["user_id"])
            else:
                attempts = row["attempts"] + 1
                terminal = error.code == 400 or (attempts >= 8 and error.code != 429)
                delay = (
                    max(5, min(int(error.retry_after), MESSAGE_SECONDS))
                    if error.code == 429
                    else min(600, 5 * 2 ** min(attempts, 7))
                )
                if error.code == 429:
                    put_setting(db, "retry_at", now + delay)
                db.execute(
                    """UPDATE telegram_outbox SET status=?,next_attempt_at=?,lease_until=0,last_error=?
                       WHERE id=? AND status='sending'""",
                    (
                        "failed" if terminal else "pending",
                        now + delay,
                        f"telegram_{error.code or 'network'}",
                        row["id"],
                    ),
                )
        if error.code == 401:
            raise
        return True
    with transaction(cfg) as db:
        db.execute(
            "UPDATE telegram_outbox SET status='sent',sent_at=?,message_id=?,lease_until=0,last_error='' WHERE id=? AND status='sending'",
            (int(time.time()), result.get("message_id"), row["id"]),
        )
    return True


def validate_bot(cfg, client):
    me = client.call("getMe")
    if me.get("username", "").lower() != cfg.telegram_bot_username.lower():
        raise RuntimeError("TELEGRAM_BOT_USERNAME does not match this token.")
    if client.call("getWebhookInfo").get("url"):
        raise RuntimeError(
            "This bot already has a webhook. Use a dedicated ParcelHub bot with no webhook."
        )
    with transaction(cfg) as db:
        old = setting(db, "bot_id", "")
        if old and old != str(me["id"]):
            raise RuntimeError(
                "This database is linked to another Telegram bot. Reuse the original bot."
            )
        put_setting(db, "bot_id", me["id"])


def run_cycle(cfg, client):
    with transaction(cfg) as db:
        offset = int(setting(db, "offset"))
        retry_at = int(setting(db, "retry_at"))
    if retry_at > int(time.time()):
        time.sleep(max(0, min(10, retry_at - int(time.time()))))
        return
    updates = client.call(
        "getUpdates",
        offset=offset,
        timeout=10,
        limit=50,
        allowed_updates=["message", "my_chat_member"],
    )
    with transaction(cfg) as db:
        put_setting(db, "heartbeat", int(time.time()))
    for update in updates:
        reply = process_update(cfg, update)
        if reply:
            try:
                client.call(
                    "sendMessage",
                    chat_id=reply[0],
                    text=reply[1],
                    **(reply[2] if len(reply) > 2 else {}),
                )
            except TelegramError as error:
                if error.code == 429:
                    with transaction(cfg) as db:
                        put_setting(
                            db, "retry_at", int(time.time()) + max(5, error.retry_after)
                        )
                if error.code in (401, 429):
                    raise
                # Order/draft changes are durable even if the reply cannot be sent.
                LOG.warning("Telegram acknowledgement failed (%s)", error.code)
    for _ in range(10):
        if not deliver_one(cfg, client):
            break
    with transaction(cfg) as db:
        put_setting(db, "heartbeat", int(time.time()))


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    cfg = Settings.from_env()
    if not cfg.telegram_enabled:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN and TELEGRAM_BOT_USERNAME first.")
    initialize(cfg)
    client = TelegramClient(cfg.telegram_bot_token)
    try:
        validate_bot(cfg, client)
        LOG.info("Telegram worker started. Run only one worker for this bot.")
        while True:
            try:
                run_cycle(cfg, client)
            except TelegramError as error:
                if error.code == 401:
                    raise
                LOG.warning("Telegram unavailable (%s); retrying", error.code)
                time.sleep(max(5, min(int(error.retry_after) or 5, 60)))
    except KeyboardInterrupt:
        pass
    except (TelegramError, RuntimeError) as error:
        raise SystemExit(str(error)) from None
    finally:
        with transaction(cfg) as db:
            put_setting(db, "heartbeat", 0)


if __name__ == "__main__":
    main()
