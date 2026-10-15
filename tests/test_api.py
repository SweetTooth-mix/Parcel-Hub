import hashlib
import hmac
import json
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.database import transaction
from app.jobs import housekeeping
from app.service import fees


@pytest.fixture
def setup(tmp_path):
    clients = []

    def make(**kwargs):
        cfg = Settings(
            str(tmp_path / f"db-{len(clients)}.sqlite3"), "test-secret-" * 4, **kwargs
        )
        client = TestClient(create_app(cfg))
        client.__enter__()
        clients.append(client)
        return client, cfg

    yield make
    for c in clients:
        c.__exit__(None, None, None)


@pytest.fixture
def client(setup):
    return setup()[0]


def login(client, role="recipient"):
    r = client.post("/api/auth/demo", json={"role": role})
    assert r.status_code == 200, r.text
    client.headers["X-CSRF-Token"] = r.json()["csrf"]
    return r.json()["user"]


def verify(client, code="482910"):
    r = client.post("/api/kiosk/verify", json={"code": code})
    assert r.status_code == 200, r.text
    return {"token": r.json()["token"]}


def pay(client, t):
    r = client.post("/api/kiosk/payment", json=t)
    assert r.status_code == 200, r.text
    pid = r.json()["payment"]["id"]
    r = client.post(f"/api/kiosk/payment/{pid}/simulate", json=t)
    assert r.status_code == 200, r.text
    return pid


def test_health_static_assets_and_headers(client):
    assert client.get("/api/health").json()["status"] == "ok"
    r = client.get("/")
    assert r.status_code == 200 and "ParcelHub" in r.text
    assert "script-src 'self'" in r.headers["content-security-policy"]
    for path in ["app.js", "styles.css", "favicon.svg"]:
        assert client.get("/static/" + path).status_code == 200
    assert client.get("/api/me").headers["cache-control"] == "no-store"
    assert client.get("/api/station").json()["available"] == 11


def test_auth_access_and_recipient_isolation(client):
    assert client.get("/api/parcels").status_code == 401
    login(client)
    parcels = client.get("/api/parcels").json()["parcels"]
    assert len(parcels) == 2
    assert all("otp_hash" not in p and "recipient_email" not in p for p in parcels)
    assert client.get("/api/parcels/PH-DEMO03").status_code == 404
    assert client.post("/api/parcels/PH-DEMO03/code", json={}).status_code == 403
    for endpoint in [
        "/api/admin/users",
        "/api/admin/overview",
        "/api/admin/payments",
        "/api/admin/export.csv",
        "/api/recipients",
    ]:
        assert client.get(endpoint).status_code == 403
    assert "recipient" not in json.dumps(client.get("/api/station").json())


def test_csrf_and_cross_origin(client):
    login(client)
    del client.headers["X-CSRF-Token"]
    assert client.post("/api/notifications/read", json={}).status_code == 403
    assert (
        client.post(
            "/api/auth/demo",
            json={"role": "admin"},
            headers={"Origin": "https://evil.example"},
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/auth/login",
            json={"email": "nobody@test.test", "password": "not-password"},
        ).status_code
        == 401
    )


def test_registration_cannot_escalate_role(client):
    data = {
        "name": "New Student",
        "email": "student@campus.test",
        "student_id": "STU999",
        "password": "Password2026!",
        "role": "admin",
    }
    r = client.post("/api/auth/register", json=data)
    assert r.status_code == 201 and r.json()["user"]["role"] == "recipient"
    assert client.post("/api/auth/register", json=data).status_code == 409
    assert (
        client.post(
            "/api/auth/register", json={**data, "email": "bad-email"}
        ).status_code
        == 422
    )


def test_password_change_revokes_sessions(client):
    login(client)
    r = client.post(
        "/api/auth/password",
        json={
            "current_password": "ParcelDemo2026!",
            "new_password": "NewPassword2026!",
        },
    )
    assert r.status_code == 200
    assert client.get("/api/parcels").status_code == 401
    assert (
        client.post(
            "/api/auth/login",
            json={"email": "aiman@demo.parcelhub.test", "password": "ParcelDemo2026!"},
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/auth/login",
            json={"email": "aiman@demo.parcelhub.test", "password": "NewPassword2026!"},
        ).status_code
        == 200
    )


def test_full_pickup_requires_payment_and_close(client):
    login(client)
    t = verify(client)
    assert client.post("/api/kiosk/unlock", json=t).status_code == 402
    pay(client, t)
    r = client.post("/api/kiosk/unlock", json=t)
    assert r.json()["parcel"]["status"] == "PICKUP_OPEN"
    p = client.get("/api/parcels/PH-DEMO01").json()["parcel"]
    assert p["collected_at"] is None
    assert client.post("/api/kiosk/unlock", json=t).status_code == 409
    closed = client.post("/api/kiosk/close", json={**t, "parcel_present": False})
    assert closed.json()["parcel"]["status"] == "COLLECTED"
    assert closed.json()["parcel"]["paid_cents"] == 50
    assert (
        client.post("/api/kiosk/status", json=t).json()["parcel"]["status"]
        == "COLLECTED"
    )
    assert client.post("/api/kiosk/verify", json={"code": "482910"}).status_code == 400
    assert (
        client.post("/api/kiosk/close", json={**t, "parcel_present": False}).status_code
        == 409
    )
    assert client.get("/api/station").json()["available"] == 12
    notes = client.get("/api/notifications").json()["notifications"]
    assert any(n["title"] == "Pengambilan selesai" for n in notes)


def test_parcel_left_inside_can_be_retried_without_double_charge(client):
    t = verify(client)
    pay(client, t)
    client.post("/api/kiosk/unlock", json=t)
    r = client.post("/api/kiosk/close", json={**t, "parcel_present": True})
    assert r.json()["parcel"]["status"] == "READY"
    t2 = verify(client)
    assert client.post("/api/kiosk/unlock", json=t2).status_code == 200


def test_demo_payment_is_idempotent_and_cannot_be_stolen(client):
    t = verify(client)
    pid = pay(client, t)
    assert client.post(f"/api/kiosk/payment/{pid}/simulate", json=t).status_code == 200
    assert client.post("/api/kiosk/status", json=t).json()["parcel"]["paid_cents"] == 50
    other = verify(client, "591028")
    assert (
        client.post(f"/api/kiosk/payment/{pid}/simulate", json=other).status_code == 404
    )


def test_fees_at_exact_boundaries():
    p = {
        "deposited_at": 1000,
        "fee_cents": 50,
        "paid_cents": 0,
        "status": "READY",
        "collected_at": None,
    }
    assert fees(p, 1000 + 86400)["due_cents"] == 50
    assert fees(p, 1000 + 86401)["due_cents"] == 150
    assert fees(p, 1000 + 108000)["due_cents"] == 150
    assert fees(p, 1000 + 108001)["due_cents"] == 250
    p["paid_cents"] = 150
    assert fees(p, 1000 + 108001)["due_cents"] == 100


def test_otp_expiry_and_session_expiry(setup):
    c, cfg = setup()
    t = verify(c)
    with transaction(cfg) as db:
        db.execute("UPDATE pickup_sessions SET expires_at=1")
        db.execute("UPDATE parcels SET code_expires_at=1 WHERE id='PH-DEMO01'")
    assert c.post("/api/kiosk/unlock", json=t).status_code == 401
    assert c.post("/api/kiosk/verify", json={"code": "482910"}).status_code == 400


def test_qr_is_opaque_valid_and_rotates_previous_credentials(client):
    login(client)
    first = client.post("/api/parcels/PH-DEMO01/code", json={}).json()
    assert "<svg" in first["qr_svg"] and "<path" in first["qr_svg"]
    assert len(first["otp"]) == 6 and len(first["qr_token"]) > 32
    assert client.post("/api/kiosk/verify", json={"code": "482910"}).status_code == 400
    assert (
        client.post(
            "/api/kiosk/verify", json={"code": "PARCELHUB:" + first["qr_token"]}
        ).status_code
        == 200
    )
    second = client.post("/api/parcels/PH-DEMO01/code", json={}).json()
    assert second["otp"] != first["otp"]
    assert (
        client.post("/api/kiosk/verify", json={"code": first["otp"]}).status_code == 400
    )
    assert (
        client.post("/api/kiosk/verify", json={"code": first["qr_token"]}).status_code
        == 400
    )


def test_otp_rate_limit(client):
    for _ in range(10):
        assert (
            client.post("/api/kiosk/verify", json={"code": "000000"}).status_code == 400
        )
    r = client.post("/api/kiosk/verify", json={"code": "482910"})
    assert r.status_code == 429 and "retry-after" in r.headers


def test_deposit_does_not_notify_before_close_and_owner_can_collect(client):
    login(client, "operator")
    payload = {
        "recipient_id": 1,
        "tracking": "MYTEST1001",
        "courier": "J&T Express",
        "size": "S",
        "locker_id": "A01",
    }
    r = client.post("/api/parcels", json=payload)
    assert r.status_code == 201, r.text
    pid = r.json()["parcel"]["id"]
    assert r.json()["parcel"]["status"] == "RESERVED"
    # Another parcel cannot take the reserved compartment, including while its door is open.
    assert (
        client.post(
            "/api/parcels", json={**payload, "tracking": "MYTEST1002"}
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/api/parcels",
            json={
                **payload,
                "tracking": "MYTEST1003",
                "locker_id": "C04",
                "size": "XL",
            },
        ).status_code
        == 409
    )
    r = client.post(f"/api/parcels/{pid}/deposit-close", json={"parcel_present": True})
    assert r.json()["parcel"]["status"] == "READY"
    assert client.post(f"/api/parcels/{pid}/code", json={}).status_code == 403
    login(client)
    codes = client.post(f"/api/parcels/{pid}/code", json={})
    assert codes.status_code == 200
    assert any(
        n["parcel_id"] == pid
        for n in client.get("/api/notifications").json()["notifications"]
    )
    assert verify(client, codes.json()["otp"])


def test_cancel_empty_deposit_releases_locker(client):
    login(client, "operator")
    r = client.post(
        "/api/parcels",
        json={
            "recipient_id": 1,
            "tracking": "CANCEL100",
            "courier": "SPX",
            "size": "S",
            "locker_id": "A01",
        },
    )
    pid = r.json()["parcel"]["id"]
    assert (
        client.post(
            f"/api/parcels/{pid}/deposit-close", json={"parcel_present": False}
        ).json()["parcel"]["status"]
        == "CANCELLED"
    )
    assert (
        next(
            l for l in client.get("/api/station").json()["lockers"] if l["id"] == "A01"
        )["state"]
        == "available"
    )


def test_concurrent_deposit_claims_only_one_locker(client):
    login(client, "operator")

    def reserve(i):
        return client.post(
            "/api/parcels",
            json={
                "recipient_id": 1,
                "tracking": f"RACE{i}",
                "courier": "SPX",
                "size": "S",
                "locker_id": "A01",
            },
        ).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(reserve, [1, 2])) == [201, 409]


def test_admin_maintenance_and_operator_permission(client):
    login(client, "operator")
    payload = {"enabled": True, "reason": "Pemeriksaan kunci"}
    assert client.patch("/api/admin/lockers/A01", json=payload).status_code == 403
    login(client, "admin")
    assert client.patch("/api/admin/lockers/A02", json=payload).status_code == 409
    assert client.patch("/api/admin/lockers/A01", json=payload).status_code == 200
    assert (
        client.post(
            "/api/parcels",
            json={
                "recipient_id": 1,
                "tracking": "MAINT100",
                "courier": "SPX",
                "size": "S",
                "locker_id": "A01",
            },
        ).status_code
        == 409
    )
    assert (
        client.patch(
            "/api/admin/lockers/A01", json={**payload, "enabled": False}
        ).status_code
        == 200
    )


def test_reminder_throttle_and_read_isolation(client):
    login(client, "operator")
    assert (
        client.post("/api/admin/parcels/PH-DEMO01/remind", json={}).status_code == 200
    )
    assert (
        client.post("/api/admin/parcels/PH-DEMO01/remind", json={}).status_code == 429
    )
    login(client)
    assert client.post("/api/notifications/read", json={}).status_code == 200
    assert all(
        n["read_at"] for n in client.get("/api/notifications").json()["notifications"]
    )


def test_device_acknowledgement_drives_real_state(setup):
    c, cfg = setup(hardware_mode="device", device_token="device-secret-" * 4)
    t = verify(c)
    pay(c, t)
    r = c.post("/api/kiosk/unlock", json=t)
    cid = r.json()["command_id"]
    assert r.json()["parcel"]["status"] == "UNLOCK_PENDING"
    assert (
        c.post("/api/kiosk/close", json={**t, "parcel_present": False}).status_code
        == 403
    )
    assert c.get("/api/device/commands").status_code == 401
    headers = {"Authorization": "Bearer " + cfg.device_token}
    assert any(
        x["id"] == cid
        for x in c.get("/api/device/commands", headers=headers).json()["commands"]
    )
    url = f"/api/device/commands/{cid}/events"
    assert (
        c.post(
            url, json={"event": "closed", "parcel_present": False}, headers=headers
        ).status_code
        == 409
    )
    assert (
        c.post(url, json={"event": "opened"}, headers=headers).json()["status"]
        == "PICKUP_OPEN"
    )
    assert c.post(url, json={"event": "opened"}, headers=headers).status_code == 200
    assert c.post(url, json={"event": "closed"}, headers=headers).status_code == 422
    assert (
        c.post(
            url, json={"event": "closed", "parcel_present": False}, headers=headers
        ).json()["status"]
        == "COLLECTED"
    )
    assert (
        c.post(
            url, json={"event": "closed", "parcel_present": False}, headers=headers
        ).status_code
        == 200
    )
    assert c.post("/api/kiosk/status", json=t).json()["parcel"]["status"] == "COLLECTED"


def test_stalled_command_and_manual_recovery(setup):
    c, cfg = setup(hardware_mode="device", device_token="device-secret-" * 4)
    t = verify(c)
    pay(c, t)
    c.post("/api/kiosk/unlock", json=t)
    with transaction(cfg) as db:
        db.execute("UPDATE commands SET created_at=?", (int(time.time()) - 100,))
    housekeeping(cfg)
    login(c, "admin")
    assert c.get("/api/parcels/PH-DEMO01").json()["parcel"]["status"] == "ISSUE"
    data = {
        "outcome": "restore",
        "reason": "Kabel diperiksa dan parcel masih di dalam",
        "door_closed_confirmed": False,
    }
    assert c.post("/api/admin/parcels/PH-DEMO01/resolve", json=data).status_code == 400
    assert (
        c.post(
            "/api/admin/parcels/PH-DEMO01/resolve",
            json={**data, "door_closed_confirmed": True},
        ).status_code
        == 200
    )
    p = c.get("/api/parcels/PH-DEMO01").json()["parcel"]
    assert p["status"] == "READY" and not p["door_open"]


def test_automatic_reminders_are_not_duplicated(setup):
    c, cfg = setup()
    housekeeping(cfg)
    housekeeping(cfg)
    login(c)
    notes = c.get("/api/notifications").json()["notifications"]
    assert sum(n["title"] == "Peringatan parcel lewat" for n in notes) == 1


def test_webhook_signature_exact_amount_and_replay(setup):
    c, cfg = setup(payment_secret="provider-secret-" * 4)
    t = verify(c)
    p = c.post("/api/kiosk/payment", json=t).json()["payment"]
    data = {
        "event_id": "event-001",
        "payment_id": p["id"],
        "amount_cents": 50,
        "currency": "MYR",
        "status": "succeeded",
    }

    def request(data, valid=True):
        body = json.dumps(data, separators=(",", ":")).encode()
        ts = str(int(time.time()))
        sig = hmac.new(
            cfg.payment_secret.encode(), ts.encode() + b"." + body, hashlib.sha256
        ).hexdigest()
        return c.post(
            "/api/payments/webhook",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Payment-Timestamp": ts,
                "X-Payment-Signature": sig if valid else "bad",
            },
        )

    assert request(data, False).status_code == 401
    assert request({**data, "amount_cents": 1}).status_code == 409
    assert request(data).status_code == 200
    assert request(data).json()["duplicate"] is True
    assert c.post("/api/kiosk/status", json=t).json()["parcel"]["paid_cents"] == 50


def test_export_escapes_spreadsheet_formula_and_admin_only(setup):
    c, cfg = setup()
    login(c, "admin")
    with transaction(cfg) as db:
        db.execute("UPDATE parcels SET courier='=1+1' WHERE id='PH-DEMO01'")
    r = c.get("/api/admin/export.csv")
    assert r.status_code == 200
    assert "'=1+1" in r.text and "attachment" in r.headers["content-disposition"]


def test_non_demo_requires_bootstrap_and_disables_demo(setup):
    c, cfg = setup(
        demo=False,
        admin_email="admin@campus.test",
        admin_password="LongInitialPassword!",
    )
    assert c.post("/api/auth/demo", json={"role": "admin"}).status_code == 404
    r = c.post(
        "/api/auth/login",
        json={"email": "admin@campus.test", "password": "LongInitialPassword!"},
    )
    assert r.status_code == 200
    assert c.get("/api/me").json()["demo"] is False
    assert c.get("/api/station").json()["available"] == 16


def test_database_survives_app_restart(setup):
    c, cfg = setup()
    t = verify(c)
    pay(c, t)
    c.post("/api/kiosk/unlock", json=t)
    c.post("/api/kiosk/close", json={**t, "parcel_present": False})
    with TestClient(create_app(cfg)) as other:
        login(other)
        assert (
            other.get("/api/parcels/PH-DEMO01").json()["parcel"]["status"]
            == "COLLECTED"
        )


def test_demo_database_cannot_become_production(setup):
    c, cfg = setup()
    with pytest.raises(RuntimeError, match="demo database"):
        from dataclasses import replace

        with TestClient(create_app(replace(cfg, demo=False))):
            pass
