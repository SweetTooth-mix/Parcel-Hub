"""Orders use the same transactional workflow from web sessions and linked chats."""

import json
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app import orders, service as svc, telegram as tg
from app.database import initialize, transaction
from app.main import create_app
from tests.test_api import setup, client, login, verify, pay
from tests.test_telegram import connected_app, link, update, FakeTelegram


def create(c, tracking="ORDER100", **extra):
    response = c.post(
        "/api/orders",
        json={"tracking": tracking, "courier": "SPX Express", "size": "M", **extra},
    )
    assert response.status_code == 201, response.text
    return response.json()["order"]


def action(c, oid, verb, **data):
    r = c.post(f"/api/orders/{oid}/{verb}", json=data)
    assert r.status_code == 200, r.text
    return r.json()["order"]


def complete(c, oid):
    login(c, "operator")
    action(c, oid, "accept")
    started = action(c, oid, "store")
    assert started["status"] == "RESERVED" and started["pickup_code"] is None
    assert action(c, oid, "confirm")["status"] == "READY"
    login(c)
    return c.get(f"/api/orders/{oid}").json()["order"]


def drain(cfg, fake):
    now = int(time.time())
    for i in range(30):
        tg.deliver_one(cfg, fake, now + i * 2)


def test_web_order_worker_notification_code_and_collection(connected_app):
    c, cfg = connected_app
    link(c, cfg)
    login(c, "operator")
    link(c, cfg, seq=2, chat=10004)
    login(c)
    available = c.get("/api/station").json()["available"]
    o = create(c)
    oid = o["id"]
    assert o["status"] == "PENDING" and o["parcel"] is None
    assert c.get("/api/station").json()["available"] == available
    assert create(c)["id"] == oid  # retried request does not duplicate notifications
    fake = FakeTelegram()
    drain(cfg, fake)
    assert any(p["chat_id"] == 10004 and oid in p["text"] for m, p in fake.calls)
    assert not any("Kod pengambilan:" in p["text"] for m, p in fake.calls)
    login(c, "operator")
    assert any(
        oid in n["body"] for n in c.get("/api/notifications").json()["notifications"]
    )
    action(c, oid, "accept")
    started = action(c, oid, "store")
    pid = started["parcel_id"]
    assert action(c, oid, "store")["parcel_id"] == pid
    login(c)
    assert c.get(f"/api/parcels/{pid}/code").status_code == 409
    login(c, "operator")
    assert action(c, oid, "confirm")["pickup_code"] is None  # never exposed to worker
    action(c, oid, "confirm")  # idempotent confirmation
    login(c)
    ready = c.get(f"/api/orders/{oid}").json()["order"]
    otp = ready["pickup_code"]["otp"]
    assert len(otp) == 6
    code = c.get(f"/api/parcels/{pid}/code").json()
    assert code["otp"] == otp
    assert c.get(f"/api/parcels/{pid}/code").json() == code
    assert any(
        otp in n["body"] for n in c.get("/api/notifications").json()["notifications"]
    )
    drain(cfg, fake)
    messages = [p for m, p in fake.calls if "Kod pengambilan:" in p["text"]]
    assert len(messages) == 1 and messages[0]["chat_id"] == 10001
    assert (
        otp in messages[0]["text"]
        and ready["parcel"]["locker_id"] in messages[0]["text"]
    )
    with transaction(cfg) as db:
        assert db.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 1
        assert (
            db.execute(
                "SELECT COUNT(*) FROM notification_codes WHERE parcel_id=?", (pid,)
            ).fetchone()[0]
            == 1
        )
        saved = json.dumps(
            [
                dict(x)
                for x in db.execute(
                    "SELECT body FROM notifications UNION ALL SELECT text FROM telegram_outbox"
                )
            ]
        )
        assert otp not in saved and code["qr_token"] not in saved
    session = verify(c, otp)
    pay(c, session)
    assert c.post("/api/kiosk/unlock", json=session).status_code == 200
    assert (
        c.post(
            "/api/kiosk/close", json={**session, "parcel_present": False}
        ).status_code
        == 200
    )
    done = c.get(f"/api/orders/{oid}").json()["order"]
    assert done["status"] == "COLLECTED" and done["pickup_code"] is None
    assert c.post("/api/kiosk/verify", json={"code": otp}).status_code == 400


def test_order_auth_csrf_isolation_and_assignment(client):
    c = client
    assert c.get("/api/orders").status_code == 401
    login(c)
    csrf = c.headers.pop("X-CSRF-Token")
    assert (
        c.post(
            "/api/orders", json={"tracking": "TEST001", "courier": "SPX"}
        ).status_code
        == 403
    )
    c.headers["X-CSRF-Token"] = csrf
    o = create(c)
    for verb in ("accept", "store", "confirm", "reject"):
        assert (
            c.post(
                f"/api/orders/{o['id']}/{verb}", json={"reason": "Test reason"}
            ).status_code
            == 403
        )
    reg = c.post(
        "/api/auth/register",
        json={
            "name": "Other Student",
            "email": "other@example.test",
            "student_id": "OTHER001",
            "password": "long-password-123",
        },
    )
    assert reg.status_code == 201, reg.text
    c.headers["X-CSRF-Token"] = reg.json()["csrf"]
    assert c.get("/api/orders").json()["orders"] == []
    assert c.get(f"/api/orders/{o['id']}").status_code == 404
    assert c.post(f"/api/orders/{o['id']}/cancel", json={}).status_code == 404
    assert (
        c.post(
            "/api/orders",
            json={"tracking": o["tracking"], "courier": o["courier"], "size": "M"},
        ).status_code
        == 409
    )
    login(c, "operator")
    assert (
        c.post(
            "/api/orders", json={"tracking": "STAFF001", "courier": "SPX"}
        ).status_code
        == 403
    )
    action(c, o["id"], "accept")
    login(c, "admin")
    for verb in ("accept", "store", "confirm", "reject"):
        assert (
            c.post(
                f"/api/orders/{o['id']}/{verb}", json={"reason": "Test reason"}
            ).status_code
            == 409
        )
    login(c)
    assert c.post(f"/api/orders/{o['id']}/cancel", json={}).status_code == 409


def test_cancel_reject_and_empty_deposit_retry(client):
    c = client
    login(c)
    oid = create(c)["id"]
    assert action(c, oid, "cancel")["status"] == "CANCELLED"
    oid = create(c)["id"]  # cancelled tracking can be ordered again
    login(c, "operator")
    assert action(c, oid, "reject", reason="Parcel belum tiba")["status"] == "REJECTED"
    login(c)
    oid = create(c)["id"]
    login(c, "operator")
    action(c, oid, "accept")
    first = action(c, oid, "store")
    pid = first["parcel_id"]
    assert (
        c.post(
            f"/api/parcels/{pid}/deposit-close", json={"parcel_present": False}
        ).status_code
        == 200
    )
    assert c.get(f"/api/orders/{oid}").json()["order"]["status"] == "ACCEPTED"
    second = action(c, oid, "store", size="L")
    assert second["parcel_id"] == pid and second["parcel"]["size"] == "L"
    assert action(c, oid, "confirm")["status"] == "READY"


def test_concurrent_workers_claim_once(setup):
    c, cfg = setup()
    login(c)
    oid = create(c)["id"]

    def claim(uid):
        try:
            with transaction(cfg) as db:
                worker = dict(
                    db.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
                )
                orders.accept(db, oid, worker)
            return "ok"
        except HTTPException as e:
            return e.status_code

    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(claim, [4, 5]))
    assert sorted(map(str, results)) == ["409", "ok"]
    with transaction(cfg) as db:
        assert (
            db.execute(
                "SELECT COUNT(*) FROM audit WHERE action='ORDER_ACCEPTED'"
            ).fetchone()[0]
            == 1
        )


def test_reissued_expired_and_collected_codes_not_delivered(connected_app):
    c, cfg = connected_app
    link(c, cfg)
    o = complete(c, create(c)["id"])
    pid = o["parcel_id"]
    old = c.get(f"/api/parcels/{pid}/code").json()
    session = verify(c, old["otp"])
    fresh = c.post(f"/api/parcels/{pid}/code", json={}).json()
    assert fresh["otp"] != old["otp"] and fresh["qr_token"] != old["qr_token"]
    assert c.post("/api/kiosk/verify", json={"code": old["otp"]}).status_code == 400
    assert c.post("/api/kiosk/status", json=session).status_code == 401
    fake = FakeTelegram()
    drain(cfg, fake)
    sent = "\n".join(p["text"] for m, p in fake.calls)
    assert fresh["otp"] in sent and old["otp"] not in sent
    with transaction(cfg) as db:
        assert (
            db.execute(
                "SELECT COUNT(*) FROM telegram_outbox WHERE last_error='code_no_longer_valid'"
            ).fetchone()[0]
            == 1
        )
        db.execute(
            "UPDATE parcels SET code_expires_at=? WHERE id=?",
            (int(time.time()) - 1, pid),
        )
    assert c.get(f"/api/parcels/{pid}/code").status_code == 409
    assert c.get(f"/api/orders/{o['id']}").json()["order"]["pickup_code"] is None
    reply = tg.process_update(cfg, update(2, f"/code {o['id']}"))
    regenerated = c.get(f"/api/parcels/{pid}/code").json()["otp"]
    assert regenerated in reply[1]
    t = verify(c, regenerated)
    pay(c, t)
    c.post("/api/kiosk/unlock", json=t)
    c.post("/api/kiosk/close", json={**t, "parcel_present": False})
    fake2 = FakeTelegram()
    drain(cfg, fake2)
    assert not any(regenerated in p["text"] for m, p in fake2.calls)


def test_telegram_wizard_restart_validation_and_worker_flow(connected_app):
    c, cfg = connected_app
    link(c, cfg)
    login(c, "operator")
    link(c, cfg, seq=2, chat=10004)
    seq = 2

    def say(text, chat=10001):
        nonlocal seq
        seq += 1
        result = tg.process_update(cfg, update(seq, text, chat))
        assert result is not None
        return result

    assert "1/4" in say("Order baharu")[1]
    assert "Tracking mesti" in say("x")[1]
    assert "2/4" in say("TGBOT100")[1]
    initialize(cfg)  # a restart does not lose the in-progress wizard
    say("J&T Express")
    assert "Pilih S" in say("XXL")[1]
    say("M")
    say("Kotak biru")
    response = say("Hantar order")
    with transaction(cfg) as db:
        o = dict(db.execute("SELECT * FROM orders").fetchone())
        assert o["source"] == "telegram" and o["notes"] == "Kotak biru"
        assert db.execute("SELECT COUNT(*) FROM telegram_drafts").fetchone()[0] == 0
    oid = o["id"]
    assert oid in response[1]
    assert tg.process_update(cfg, update(seq, "Hantar order")) is None
    assert "pekerja" in say(f"/accept {oid}")[1]
    assert oid in say("Tugasan", 10004)[1]
    assert "diterima" in say(f"/accept {oid}", 10004)[1]
    assert "Loker" in say(f"/store {oid}", 10004)[1]
    assert "sedia diambil" in say(f"/stored {oid}", 10004)[1]
    login(c)
    ready = c.get(f"/api/orders/{oid}").json()["order"]
    otp = ready["pickup_code"]["otp"]
    assert otp in say("Order saya")[1]
    assert otp in say(f"/code {oid}")[1]
    assert otp not in say(f"/code {oid}", 10004)[1]
    assert c.get(f"/api/parcels/{ready['parcel_id']}/code").json()["otp"] == otp
    fake = FakeTelegram()
    drain(cfg, fake)
    assert any(otp in p["text"] and p["chat_id"] == 10001 for m, p in fake.calls)


def test_telegram_draft_expiry_cancel_and_unlinked_account(connected_app):
    c, cfg = connected_app
    assert "Daftar/log masuk" in tg.process_update(cfg, update(1, "/order"))[1]
    link(c, cfg, seq=2)
    tg.process_update(cfg, update(3, "/order"))
    tg.process_update(cfg, update(4, "DRAFT100"))
    assert "Draf dibatalkan" in tg.process_update(cfg, update(5, "Batal"))[1]
    tg.process_update(cfg, update(6, "/order"))
    with transaction(cfg) as db:
        db.execute("UPDATE telegram_drafts SET expires_at=0")
    assert "Draf order tamat" in tg.process_update(cfg, update(7, "EXPIRED100"))[1]
    assert (
        tg.process_update(cfg, update(8, "/order", chat={"id": 10001, "type": "group"}))
        is None
    )
    with transaction(cfg) as db:
        assert db.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 0


def test_device_storage_requires_physical_acknowledgement(setup):
    c, cfg = setup(hardware_mode="device", device_token="device-secret-" * 4)
    login(c)
    oid = create(c)["id"]
    login(c, "operator")
    action(c, oid, "accept")
    o = action(c, oid, "store")
    assert c.post(f"/api/orders/{oid}/confirm", json={}).status_code == 403
    assert (
        c.post(
            f"/api/parcels/{o['parcel_id']}/deposit-close",
            json={"parcel_present": True},
        ).status_code
        == 403
    )
    headers = {"Authorization": "Bearer " + cfg.device_token}
    cmd = next(
        x
        for x in c.get("/api/device/commands", headers=headers).json()["commands"]
        if x["parcel_id"] == o["parcel_id"]
    )
    url = f"/api/device/commands/{cmd['id']}/events"
    assert (
        c.post(
            url, headers=headers, json={"event": "closed", "parcel_present": True}
        ).status_code
        == 409
    )
    c.post(url, headers=headers, json={"event": "opened"})
    login(c)
    assert c.get(f"/api/orders/{oid}").json()["order"]["pickup_code"] is None
    assert (
        c.post(
            url, headers=headers, json={"event": "closed", "parcel_present": True}
        ).json()["status"]
        == "READY"
    )
    assert c.get(f"/api/orders/{oid}").json()["order"]["pickup_code"] is not None


def test_existing_v2_database_upgrades_with_accounts_and_pending_delivery(
    connected_app,
):
    c, cfg = connected_app
    link(c, cfg)
    before = c.get("/api/parcels").json()
    with transaction(cfg) as db:
        svc.notify(db, 1, None, "Preserve", "Pending message")
        for table in (
            "notification_codes",
            "pickup_credentials",
            "telegram_drafts",
            "orders",
        ):
            db.execute("DROP TABLE " + table)
        db.execute("PRAGMA user_version=2")
    initialize(cfg)
    assert c.get("/api/parcels").json() == before
    assert c.get("/api/telegram").json()["connected"]
    assert create(c)["status"] == "PENDING"
    with transaction(cfg) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 3
        assert (
            db.execute(
                "SELECT COUNT(*) FROM telegram_outbox WHERE status='pending'"
            ).fetchone()[0]
            == 2
        )
