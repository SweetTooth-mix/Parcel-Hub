import json
import re
import time
from dataclasses import replace
from io import BytesIO
from urllib.error import HTTPError, URLError

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.database import initialize, transaction
from app.main import create_app
from app import service as svc, telegram as tg
from tests.test_api import login, verify, pay


@pytest.fixture
def connected_app(tmp_path):
    cfg = Settings(
        str(tmp_path / "telegram.sqlite3"),
        "secret-for-telegram-tests" * 2,
        telegram_bot_token="123:fake-test-token",
        telegram_bot_username="ParcelHubTestBot",
    )
    with TestClient(create_app(cfg)) as client:
        login(client)
        with transaction(cfg) as db:
            tg.put_setting(db, "heartbeat", int(time.time()))
        yield client, cfg


def update(seq, text, chat_id=10001, **extra):
    message = {
        "chat": {"id": chat_id, "type": "private"},
        "from": {"id": chat_id, "first_name": "Student", "username": "student"},
        "text": text,
    }
    message.update(extra)
    return {"update_id": seq, "message": message}


def link(client, cfg, seq=1, chat=10001):
    response = client.post("/api/telegram/link", json={})
    assert response.status_code == 200, response.text
    raw = response.json()["url"].split("start=")[1]
    reply = tg.process_update(cfg, update(seq, "/start " + raw, chat))
    assert "disambungkan" in reply[1]
    return raw


class FakeTelegram:
    def __init__(self, error=None, updates=None):
        self.calls = []
        self.error = error
        self.updates = updates or []

    def call(self, method, **params):
        self.calls.append((method, params))
        if self.error:
            raise self.error
        return {
            "getMe": {"id": 123, "username": "ParcelHubTestBot"},
            "getWebhookInfo": {"url": ""},
            "getUpdates": self.updates,
            "sendMessage": {"message_id": len(self.calls)},
        }[method]


def queue(
    cfg,
    title="Parcel sedia diambil",
    body="Parcel di loker A02. Dapatkan kod di portal.",
):
    with transaction(cfg) as db:
        svc.notify(db, 1, "PH-DEMO01", title, body)


def test_api_auth_csrf_disabled_and_worker_readiness(connected_app):
    client, cfg = connected_app
    status = client.get("/api/telegram").json()
    assert status["ready"] and not status["connected"]
    assert "chat_id" not in status and "token" not in json.dumps(status)
    csrf = client.headers.pop("X-CSRF-Token")
    for path in ("link", "disconnect", "test"):
        assert client.post("/api/telegram/" + path, json={}).status_code == 403
    client.headers["X-CSRF-Token"] = csrf
    with transaction(cfg) as db:
        tg.put_setting(db, "heartbeat", 0)
    assert client.post("/api/telegram/link", json={}).status_code == 503
    client.cookies.clear()
    assert client.get("/api/telegram").status_code == 401
    with TestClient(
        create_app(replace(cfg, telegram_bot_token="", telegram_bot_username=""))
    ) as disabled:
        login(disabled)
        assert disabled.get("/api/telegram").json()["enabled"] is False
        assert disabled.post("/api/telegram/link", json={}).status_code == 503


def test_link_is_private_hashed_single_use_and_account_scoped(connected_app):
    client, cfg = connected_app
    response = client.post("/api/telegram/link", json={}).json()
    raw = response["url"].split("start=")[1]
    assert len(raw) == 43 and response["expires_at"] > int(time.time())
    with transaction(cfg) as db:
        assert (
            raw not in db.execute("SELECT token_hash FROM telegram_links").fetchone()[0]
        )
    assert (
        tg.process_update(
            cfg,
            update(1, "/start " + raw, **{"chat": {"id": -100, "type": "group"}}),
        )
        is None
    )
    assert (
        tg.process_update(cfg, update(2, "/start " + raw, **{"from": {"id": 99999}}))
        is None
    )
    assert not client.get("/api/telegram").json()["connected"]
    assert "disambungkan" in tg.process_update(cfg, update(3, "/start " + raw))[1]
    assert tg.process_update(cfg, update(3, "/start " + raw)) is None  # replayed update
    assert "tidak sah" in tg.process_update(cfg, update(4, "/start " + raw, 20002))[1]
    status = client.get("/api/telegram").json()
    assert status["connected"] and status["display_name"] == "@student"
    assert client.post("/api/telegram/link", json={}).status_code == 409
    with transaction(cfg) as db:
        assert (
            db.execute("SELECT COUNT(*) FROM telegram_outbox").fetchone()[0] == 0
        )  # no inbox history replay
    login(client, "operator")
    assert client.get("/api/telegram").json()["connected"] is False
    response = client.post("/api/telegram/link", json={}).json()
    other = response["url"].split("start=")[1]
    assert "sudah mempunyai" in tg.process_update(cfg, update(5, "/start " + other))[1]
    client.post("/api/telegram/disconnect", json={})
    with transaction(cfg) as db:
        assert db.execute("SELECT user_id FROM telegram_accounts").fetchone()[0] == 1


def test_expiry_regeneration_and_password_change_revoke_links(connected_app):
    client, cfg = connected_app
    first = client.post("/api/telegram/link", json={}).json()["url"].split("start=")[1]
    second = client.post("/api/telegram/link", json={}).json()["url"].split("start=")[1]
    assert "tidak sah" in tg.process_update(cfg, update(1, "/start " + first))[1]
    with transaction(cfg) as db:
        db.execute("UPDATE telegram_links SET expires_at=0")
    assert "tidak sah" in tg.process_update(cfg, update(2, "/start " + second))[1]
    third = client.post("/api/telegram/link", json={}).json()["url"].split("start=")[1]
    r = client.post(
        "/api/auth/password",
        json={
            "current_password": "ParcelDemo2026!",
            "new_password": "UpdatedPassword2026!",
        },
    )
    assert r.status_code == 200
    assert "tidak sah" in tg.process_update(cfg, update(3, "/start " + third))[1]


def test_inbox_and_outbox_are_atomic_and_delivery_survives_restart(connected_app):
    client, cfg = connected_app
    queue(cfg)  # unlinked inbox item, no Telegram queue
    link(client, cfg)
    with pytest.raises(RuntimeError):
        with transaction(cfg) as db:
            svc.notify(db, 1, None, "Rollback", "Must not send")
            raise RuntimeError("Simulated failed transaction")
    queue(cfg)
    initialize(cfg)  # idempotent migration; retain pending queue
    fake = FakeTelegram()
    assert tg.deliver_one(cfg, fake)
    assert not tg.deliver_one(cfg, fake)
    assert len(fake.calls) == 1 and fake.calls[0][1]["chat_id"] == 10001
    assert "482910" not in fake.calls[0][1]["text"]
    with transaction(cfg) as db:
        assert db.execute("SELECT COUNT(*) FROM telegram_outbox").fetchone()[0] == 1
        assert db.execute("SELECT status FROM telegram_outbox").fetchone()[0] == "sent"
        assert not db.execute(
            "SELECT 1 FROM notifications WHERE title='Rollback'"
        ).fetchone()


@pytest.mark.parametrize(
    "error", [tg.TelegramError(), tg.TelegramError(500), tg.TelegramError(429, 45)]
)
def test_temporary_delivery_failure_retries_without_losing_inbox(connected_app, error):
    client, cfg = connected_app
    link(client, cfg)
    queue(cfg)
    now = int(time.time())
    assert tg.deliver_one(cfg, FakeTelegram(error), now)
    with transaction(cfg) as db:
        row = db.execute("SELECT * FROM telegram_outbox").fetchone()
        assert row["status"] == "pending" and row["next_attempt_at"] > now
        assert db.execute(
            "SELECT 1 FROM notifications WHERE id=?", (row["notification_id"],)
        ).fetchone()
        retry_at = row["next_attempt_at"]
    assert not tg.deliver_one(cfg, FakeTelegram(), now)
    assert tg.deliver_one(cfg, FakeTelegram(), retry_at)
    assert client.get("/api/telegram").json()["last_sent_at"]


@pytest.mark.parametrize("action", ["portal", "stop", "blocked", "event"])
def test_disconnect_cancels_queue_without_redirecting_it(connected_app, action):
    client, cfg = connected_app
    link(client, cfg)
    queue(cfg)
    if action == "portal":
        assert client.post("/api/telegram/disconnect", json={}).status_code == 200
    elif action == "stop":
        assert "dihentikan" in tg.process_update(cfg, update(2, "/stop"))[1]
    elif action == "blocked":
        tg.deliver_one(cfg, FakeTelegram(tg.TelegramError(403)))
    else:
        tg.process_update(
            cfg,
            {
                "update_id": 2,
                "my_chat_member": {
                    "chat": {"id": 10001, "type": "private"},
                    "new_chat_member": {"status": "kicked"},
                },
            },
        )
    assert not client.get("/api/telegram").json()["connected"]
    link(client, cfg, seq=3, chat=20002)
    fake = FakeTelegram()
    assert not tg.deliver_one(cfg, fake)
    assert not fake.calls
    with transaction(cfg) as db:
        assert (
            db.execute("SELECT status FROM telegram_outbox").fetchone()[0]
            == "cancelled"
        )


def test_test_message_rate_limit_and_failed_status(connected_app):
    client, cfg = connected_app
    link(client, cfg)
    assert client.post("/api/telegram/test", json={}).json() == {"queued": True}
    assert client.post("/api/telegram/test", json={}).status_code == 429
    assert client.get("/api/telegram").json()["pending"] == 1
    tg.deliver_one(cfg, FakeTelegram(tg.TelegramError(400)))
    status = client.get("/api/telegram").json()
    assert status["failed"] == 1 and status["last_sent_at"] is None


def test_actual_pickup_event_queues_notification(connected_app):
    client, cfg = connected_app
    link(client, cfg)
    session = verify(client)
    pay(client, session)
    assert client.post("/api/kiosk/unlock", json=session).status_code == 200
    assert (
        client.post(
            "/api/kiosk/close", json={**session, "parcel_present": False}
        ).status_code
        == 200
    )
    fake = FakeTelegram()
    assert tg.deliver_one(cfg, fake)
    text = fake.calls[0][1]["text"]
    assert "Pengambilan selesai" in text and "RM0.50" in text
    assert not re.search(r"\b482910\b", text)


def test_worker_polls_persists_offset_and_acknowledges_link(connected_app):
    client, cfg = connected_app
    raw = client.post("/api/telegram/link", json={}).json()["url"].split("start=")[1]
    fake = FakeTelegram(updates=[update(20, "/start " + raw)])
    tg.validate_bot(cfg, fake)
    tg.run_cycle(cfg, fake)
    assert client.get("/api/telegram").json()["connected"]
    assert any(
        c[0] == "sendMessage" and "disambungkan" in c[1]["text"] for c in fake.calls
    )
    fake.calls.clear()
    tg.run_cycle(cfg, fake)
    assert fake.calls[0][0] == "getUpdates" and fake.calls[0][1]["offset"] == 21
    assert not any(c[0] == "sendMessage" for c in fake.calls)


def test_expired_messages_cancel_and_crashed_sends_recover(connected_app):
    client, cfg = connected_app
    link(client, cfg)
    queue(cfg)
    now = int(time.time())
    with transaction(cfg) as db:
        db.execute(
            "UPDATE telegram_outbox SET status='sending',lease_until=?", (now + 60,)
        )
    assert not tg.deliver_one(cfg, FakeTelegram(), now)
    assert tg.deliver_one(cfg, FakeTelegram(), now + 61)
    queue(cfg)
    with transaction(cfg) as db:
        db.execute("UPDATE telegram_outbox SET created_at=0 WHERE status='pending'")
    assert not tg.deliver_one(cfg, FakeTelegram(), now + 62)


def test_transport_never_exposes_token_in_errors(monkeypatch):
    secret = "123:super-secret-token"

    def fail(*args, **kwargs):
        raise HTTPError(
            "https://api.telegram.org/bot" + secret + "/sendMessage",
            429,
            secret,
            {},
            BytesIO(b'{"parameters":{"retry_after":35}}'),
        )

    monkeypatch.setattr(tg, "urlopen", fail)
    with pytest.raises(tg.TelegramError) as error:
        tg.TelegramClient(secret).call("sendMessage", chat_id=1, text="test")
    assert error.value.retry_after == 35 and secret not in str(error.value)

    def network_fail(*args, **kwargs):
        raise URLError(secret)

    monkeypatch.setattr(tg, "urlopen", network_fail)
    with pytest.raises(tg.TelegramError) as error:
        tg.TelegramClient(secret).call("getUpdates")
    assert secret not in str(error.value)


def test_existing_v1_database_upgrades_without_losing_records(connected_app):
    client, cfg = connected_app
    before = client.get("/api/parcels").json()
    with transaction(cfg) as db:
        db.execute("DROP TABLE telegram_outbox")
        db.execute("DROP TABLE telegram_links")
        db.execute("DROP TABLE telegram_accounts")
        db.execute("PRAGMA user_version=1")
    initialize(cfg)
    assert client.get("/api/parcels").json() == before
    link(client, cfg)
    queue(cfg)
    assert tg.deliver_one(cfg, FakeTelegram())
    with transaction(cfg) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 2


def test_worker_rejects_wrong_bot_and_existing_webhook(connected_app):
    _, cfg = connected_app
    fake = FakeTelegram()
    with pytest.raises(RuntimeError, match="does not match"):
        tg.validate_bot(replace(cfg, telegram_bot_username="OtherBot"), fake)

    class WebhookBot(FakeTelegram):
        def call(self, method, **params):
            if method == "getWebhookInfo":
                return {"url": "https://existing.example/webhook"}
            return super().call(method, **params)

    with pytest.raises(RuntimeError, match="already has a webhook"):
        tg.validate_bot(cfg, WebhookBot())
    with transaction(cfg) as db:
        tg.put_setting(db, "bot_id", 999)
    with pytest.raises(RuntimeError, match="another Telegram bot"):
        tg.validate_bot(cfg, fake)


def test_environment_requires_both_bot_fields_and_redacts_token(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "env-data"))
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:fake-secret")
    monkeypatch.setenv("TELEGRAM_BOT_USERNAME", "")
    with pytest.raises(RuntimeError, match="Set both"):
        Settings.from_env()
    monkeypatch.setenv("TELEGRAM_BOT_USERNAME", "@ParcelHubTestBot")
    cfg = Settings.from_env()
    assert cfg.telegram_enabled and cfg.telegram_bot_username == "ParcelHubTestBot"
    assert "fake-secret" not in repr(cfg)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "invalid/secret")
    with pytest.raises(RuntimeError, match="invalid format") as error:
        Settings.from_env()
    assert "invalid/secret" not in str(error.value)
