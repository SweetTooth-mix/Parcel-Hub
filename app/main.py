from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Literal
import asyncio
import logging
import csv
import hashlib
import hmac
import io
import json
import secrets
import sqlite3
import time

import qrcode
import qrcode.image.svg
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from .config import Settings
from .database import initialize, transaction
from .security import password_hash, password_matches, fingerprint, token
from . import service as svc
from .jobs import housekeeping

STATIC = Path(__file__).parent / "static"


class Login(BaseModel):
    email: str = Field(min_length=3, max_length=160)
    password: str = Field(min_length=1, max_length=128)


class Register(Login):
    name: str = Field(min_length=2, max_length=80)
    student_id: str = Field(min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9-]+$")

    @field_validator("email")
    @classmethod
    def valid_email(cls, value):
        value = value.strip().lower()
        if (
            "@" not in value
            or "." not in value.split("@")[-1]
            or any(c.isspace() for c in value)
        ):
            raise ValueError("Alamat e-mel tidak sah.")
        return value

    @field_validator("password")
    @classmethod
    def strong_password(cls, value):
        if len(value) < 10:
            raise ValueError("Kata laluan sekurang-kurangnya 10 aksara.")
        return value


class DemoLogin(BaseModel):
    role: Literal["recipient", "operator", "admin"]


class Deposit(BaseModel):
    recipient_id: int
    tracking: str = Field(min_length=4, max_length=60, pattern=r"^[a-zA-Z0-9-]+$")
    courier: str = Field(min_length=2, max_length=50)
    size: Literal["S", "M", "L", "XL"]
    locker_id: str | None = Field(default=None, max_length=8)


class Verify(BaseModel):
    code: str = Field(min_length=6, max_length=100)


class PickupToken(BaseModel):
    token: str = Field(min_length=20, max_length=100)


class DoorClose(BaseModel):
    parcel_present: bool


class PickupClose(PickupToken):
    parcel_present: bool = False


class Maintain(BaseModel):
    enabled: bool
    reason: str = Field(min_length=5, max_length=300)


class DeviceEvent(BaseModel):
    event: Literal["opened", "closed", "fault"]
    parcel_present: bool | None = None
    detail: str = Field(default="", max_length=300)


class Resolve(BaseModel):
    outcome: Literal["restore", "collected", "cancel"]
    reason: str = Field(min_length=10, max_length=300)
    door_closed_confirmed: bool


class NewUser(Register):
    role: Literal["recipient", "operator", "admin"] = "recipient"


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=10, max_length=128)


def create_app(settings=None):
    cfg = settings or Settings.from_env()
    dummy_password = password_hash(token())

    @asynccontextmanager
    async def lifespan(app):
        initialize(cfg)

        async def periodic():
            while True:
                await asyncio.sleep(60)
                try:
                    await asyncio.to_thread(housekeeping, cfg)
                except Exception:
                    logging.getLogger("parcelhub").exception("Housekeeping failed")

        task = asyncio.create_task(periodic())
        try:
            yield
        finally:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    app = FastAPI(
        title="ParcelHub API",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/api/docs" if cfg.demo else None,
        redoc_url=None,
    )
    app.state.settings = cfg

    @app.middleware("http")
    async def safeguards(req: Request, call_next):
        if req.method not in ("GET", "HEAD", "OPTIONS"):
            origin = req.headers.get("origin")
            expected = cfg.origin or str(req.base_url).rstrip("/")
            if origin and origin.rstrip("/") != expected:
                return JSONResponse(
                    {"detail": "Origin tidak dibenarkan."}, status_code=403
                )
            if len(await req.body()) > 32768:
                return JSONResponse(
                    {"detail": "Permintaan terlalu besar."}, status_code=413
                )
        limited = {
            "/api/auth/login": (20, 900),
            "/api/auth/register": (5, 3600),
            "/api/kiosk/verify": (10, 300),
        }
        if req.method == "POST" and req.url.path in limited:
            limit, window = limited[req.url.path]
            now = int(time.time())
            ip = req.client.host if req.client else "local"
            key = fingerprint(ip + "|" + req.url.path, cfg.secret)
            with transaction(cfg) as db:
                db.execute("DELETE FROM rate_limits WHERE expires_at<=?", (now,))
                row = db.execute(
                    "SELECT * FROM rate_limits WHERE key=?", (key,)
                ).fetchone()
                if row and row["count"] >= limit:
                    return JSONResponse(
                        {"detail": "Terlalu banyak cubaan. Sila cuba semula kemudian."},
                        status_code=429,
                        headers={"Retry-After": str(row["expires_at"] - now)},
                    )
                db.execute(
                    "INSERT INTO rate_limits(key,count,expires_at) VALUES (?,1,?) ON CONFLICT(key) DO UPDATE SET count=count+1",
                    (key, now + window),
                )
        response = await call_next(req)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Permissions-Policy"] = (
            "camera=(self), microphone=(), geolocation=()"
        )
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; font-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        )
        if req.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        if cfg.secure_cookies:
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response

    @app.exception_handler(sqlite3.IntegrityError)
    async def conflict(req, exc):
        return JSONResponse(
            {
                "detail": "Rekod bertindih atau loker sudah digunakan. Muat semula dan cuba lagi."
            },
            status_code=409,
        )

    def user(db, req, roles=None, optional=False):
        raw = req.cookies.get("ph_session", "")
        row = db.execute(
            """SELECT u.*,s.csrf,s.expires_at FROM sessions s JOIN users u ON u.id=s.user_id
                            WHERE s.token_hash=? AND s.expires_at>?""",
            (fingerprint(raw, cfg.secret), int(time.time())),
        ).fetchone()
        if not row:
            if optional:
                return None
            raise HTTPException(401, "Sila log masuk semula.")
        if roles and row["role"] not in roles:
            raise HTTPException(403, "Akses tidak dibenarkan untuk akaun ini.")
        if req.method not in ("GET", "HEAD") and not hmac.compare_digest(
            req.headers.get("x-csrf-token", ""), row["csrf"]
        ):
            raise HTTPException(403, "Sesi tidak sah. Muat semula halaman.")
        return dict(row)

    def public_user(u):
        return {key: u[key] for key in ("id", "name", "email", "student_id", "role")}

    def login_response(db, u, response, req):
        now = int(time.time())
        db.execute("DELETE FROM sessions WHERE expires_at<=?", (now,))
        # Rotate any existing browser session on sign in.
        if req.cookies.get("ph_session"):
            db.execute(
                "DELETE FROM sessions WHERE token_hash=?",
                (fingerprint(req.cookies["ph_session"], cfg.secret),),
            )
        session, csrf = token(), token()
        db.execute(
            "INSERT INTO sessions VALUES (?,?,?,?)",
            (
                fingerprint(session, cfg.secret),
                u["id"],
                csrf,
                now + cfg.session_hours * 3600,
            ),
        )
        response.set_cookie(
            "ph_session",
            session,
            httponly=True,
            secure=cfg.secure_cookies,
            samesite="strict",
            max_age=cfg.session_hours * 3600,
            path="/",
        )
        audit_actor = u["id"]
        svc.audit(db, audit_actor, "LOGIN")
        return {"user": public_user(u), "csrf": csrf}

    def device_auth(req):
        expected = "Bearer " + cfg.device_token
        svc.require(
            bool(cfg.device_token)
            and hmac.compare_digest(req.headers.get("authorization", ""), expected),
            "Peranti tidak dibenarkan.",
            401,
        )

    def require_demo():
        svc.require(cfg.demo, "Fungsi ini hanya tersedia dalam mod demo.", 404)

    @app.get("/api/health")
    def health():
        with transaction(cfg) as db:
            db.execute("SELECT 1").fetchone()
        return {"status": "ok", "version": "1.0.0"}

    @app.get("/api/me")
    def me(req: Request):
        with transaction(cfg) as db:
            u = user(db, req, optional=True)
            return {
                "user": public_user(u) if u else None,
                "csrf": u["csrf"] if u else None,
                "demo": cfg.demo,
                "hardware_mode": cfg.hardware_mode,
                "station": {
                    "id": "PAP-01",
                    "name": "Pusat Aktiviti Pelajar",
                    "location": "Kampus · PAP",
                },
                "pricing": {
                    "small_cents": 50,
                    "large_cents": 100,
                    "free_hours": 24,
                    "late_cents": 100,
                    "late_block_hours": 6,
                },
            }

    @app.post("/api/auth/login")
    def login(data: Login, req: Request, response: Response):
        with transaction(cfg) as db:
            u = db.execute(
                "SELECT * FROM users WHERE email=?", (data.email.strip().lower(),)
            ).fetchone()
            valid_password = password_matches(
                data.password, u["password"] if u else dummy_password
            )
            svc.require(
                u is not None and valid_password,
                "E-mel atau kata laluan tidak tepat.",
                401,
            )
            return login_response(db, dict(u), response, req)

    @app.post("/api/auth/demo")
    def demo_login(data: DemoLogin, req: Request, response: Response):
        require_demo()
        emails = {"recipient": "aiman", "operator": "operator", "admin": "admin"}
        with transaction(cfg) as db:
            u = db.execute(
                "SELECT * FROM users WHERE email=?",
                (emails[data.role] + "@demo.parcelhub.test",),
            ).fetchone()
            svc.require(u is not None, "Akaun demo tiada.", 404)
            return login_response(db, dict(u), response, req)

    @app.post("/api/auth/register", status_code=201)
    def register(data: Register, req: Request, response: Response):
        with transaction(cfg) as db:
            uid = db.execute(
                "INSERT INTO users(name,email,student_id,password,role,created_at) VALUES (?,?,?,?,?,?)",
                (
                    data.name.strip(),
                    data.email,
                    data.student_id.upper(),
                    password_hash(data.password),
                    "recipient",
                    int(time.time()),
                ),
            ).lastrowid
            u = dict(db.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone())
            return login_response(db, u, response, req)

    @app.post("/api/auth/logout")
    def logout(req: Request, response: Response):
        with transaction(cfg) as db:
            user(db, req)
            db.execute(
                "DELETE FROM sessions WHERE token_hash=?",
                (fingerprint(req.cookies.get("ph_session", ""), cfg.secret),),
            )
        response.delete_cookie("ph_session", path="/")
        return {"ok": True}

    @app.post("/api/auth/password")
    def change_password(data: PasswordChange, req: Request, response: Response):
        with transaction(cfg) as db:
            u = user(db, req)
            svc.require(
                password_matches(data.current_password, u["password"]),
                "Kata laluan semasa tidak tepat.",
                400,
            )
            db.execute(
                "UPDATE users SET password=? WHERE id=?",
                (password_hash(data.new_password), u["id"]),
            )
            db.execute("DELETE FROM sessions WHERE user_id=?", (u["id"],))
            svc.audit(db, u["id"], "PASSWORD_CHANGED")
        response.delete_cookie("ph_session", path="/")
        return {"ok": True}

    @app.get("/api/station")
    def station():
        with transaction(cfg) as db:
            rows = db.execute(
                """SELECT l.*,p.status parcel_status FROM lockers l LEFT JOIN parcels p
                                ON p.locker_id=l.id AND p.status NOT IN ('COLLECTED','CANCELLED') ORDER BY l.id"""
            ).fetchall()
            result = []
            for row in rows:
                l = dict(row)
                l["state"] = (
                    "maintenance"
                    if l["maintenance"]
                    else (
                        "open"
                        if l["door_open"]
                        else "occupied" if l["parcel_status"] else "available"
                    )
                )
                l.pop("parcel_status")
                result.append(l)
            return {
                "lockers": result,
                "available": sum(x["state"] == "available" for x in result),
                "occupied": sum(x["state"] == "occupied" for x in result),
                "total": len(result),
            }

    @app.get("/api/parcels")
    def list_parcels(req: Request):
        with transaction(cfg) as db:
            u = user(db, req)
            staff = u["role"] != "recipient"
            ids = db.execute(
                "SELECT id FROM parcels "
                + ("" if staff else "WHERE recipient_id=? ")
                + "ORDER BY created_at DESC,id DESC LIMIT 500",
                () if staff else (u["id"],),
            ).fetchall()
            return {
                "parcels": [
                    svc.serialize_parcel(svc.parcel(db, r["id"]), staff) for r in ids
                ]
            }

    @app.get("/api/parcels/{pid}")
    def get_parcel(pid: str, req: Request):
        with transaction(cfg) as db:
            u = user(db, req)
            p = svc.parcel(db, pid)
            svc.require(
                u["role"] != "recipient" or u["id"] == p["recipient_id"],
                "Parcel tidak dijumpai.",
                404,
            )
            c = db.execute(
                "SELECT id,state,kind FROM commands WHERE parcel_id=? ORDER BY created_at DESC,id DESC LIMIT 1",
                (pid,),
            ).fetchone()
            return {
                "parcel": svc.serialize_parcel(p, u["role"] != "recipient"),
                "command": dict(c) if c else None,
            }

    @app.post("/api/parcels/{pid}/code")
    def code(pid: str, req: Request):
        with transaction(cfg) as db:
            u = user(db, req)
            p = svc.parcel(db, pid)
            svc.require(
                u["id"] == p["recipient_id"],
                "Kod hanya boleh dilihat oleh penerima.",
                403,
            )
            result = svc.generate_code(db, p, cfg)
            # A standards-compliant QR encodes the opaque pickup credential, never personal details.
            qr = qrcode.make(
                "PARCELHUB:" + result["qr_token"],
                image_factory=qrcode.image.svg.SvgPathImage,
                box_size=8,
                border=4,
            )
            output = io.BytesIO()
            qr.save(output)
            result["qr_svg"] = output.getvalue().decode()
            svc.audit(db, u["id"], "PICKUP_CODE_REISSUED", pid)
            return result

    @app.get("/api/notifications")
    def notifications(req: Request):
        with transaction(cfg) as db:
            u = user(db, req)
            return {
                "notifications": [
                    dict(r)
                    for r in db.execute(
                        "SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC,id DESC LIMIT 100",
                        (u["id"],),
                    )
                ]
            }

    @app.post("/api/notifications/read")
    def read_notifications(req: Request):
        with transaction(cfg) as db:
            u = user(db, req)
            db.execute(
                "UPDATE notifications SET read_at=? WHERE user_id=? AND read_at IS NULL",
                (int(time.time()), u["id"]),
            )
        return {"ok": True}

    @app.get("/api/recipients")
    def recipients(req: Request):
        with transaction(cfg) as db:
            user(db, req, ("operator", "admin"))
            return {
                "users": [
                    dict(r)
                    for r in db.execute(
                        "SELECT id,name,email,student_id FROM users WHERE role='recipient' ORDER BY name LIMIT 1000"
                    )
                ]
            }

    @app.post("/api/parcels", status_code=201)
    def deposit(data: Deposit, req: Request):
        with transaction(cfg) as db:
            u = user(db, req, ("operator", "admin"))
            svc.require(
                db.execute(
                    "SELECT 1 FROM users WHERE id=? AND role='recipient'",
                    (data.recipient_id,),
                ).fetchone(),
                "Pilih akaun penerima yang sah.",
                400,
            )
            rows = db.execute(
                """SELECT l.* FROM lockers l WHERE l.size=? AND l.maintenance=0 AND l.door_open=0
                               AND NOT EXISTS (SELECT 1 FROM parcels p WHERE p.locker_id=l.id AND p.status NOT IN ('COLLECTED','CANCELLED'))
                               ORDER BY l.id""",
                (data.size,),
            ).fetchall()
            eligible = [
                dict(r) for r in rows if not data.locker_id or r["id"] == data.locker_id
            ]
            svc.require(
                bool(eligible), "Tiada loker saiz ini yang tersedia. Cuba saiz lain."
            )
            locker = eligible[0]
            pid = "PH-" + secrets.token_hex(4).upper()
            db.execute(
                "INSERT INTO parcels(id,tracking,recipient_id,locker_id,courier,status,created_at,fee_cents) VALUES (?,?,?,?,?,?,?,?)",
                (
                    pid,
                    data.tracking.upper(),
                    data.recipient_id,
                    locker["id"],
                    data.courier,
                    "RESERVED",
                    int(time.time()),
                    locker["fee_cents"],
                ),
            )
            cid = svc.command(db, svc.parcel(db, pid), "DEPOSIT", cfg, u["id"])
            return {
                "parcel": svc.serialize_parcel(svc.parcel(db, pid), True),
                "command_id": cid,
            }

    @app.post("/api/parcels/{pid}/deposit-close")
    def deposit_close(pid: str, data: DoorClose, req: Request):
        svc.require(
            cfg.hardware_mode == "simulated",
            "Pengesahan mesti datang daripada peranti.",
            403,
        )
        with transaction(cfg) as db:
            u = user(db, req, ("operator", "admin"))
            p = svc.parcel(db, pid)
            svc.require(
                p["status"] == "RESERVED", "Parcel bukan dalam proses penyimpanan."
            )
            c = db.execute(
                "SELECT id FROM commands WHERE parcel_id=? AND kind='DEPOSIT' AND state='opened'",
                (pid,),
            ).fetchone()
            svc.require(c is not None, "Pintu belum disahkan terbuka.")
            return {
                "parcel": svc.serialize_parcel(
                    svc.door_event(
                        db, c["id"], "closed", data.parcel_present, str(u["id"]), cfg
                    ),
                    True,
                )
            }

    @app.post("/api/kiosk/verify")
    def verify(data: Verify):
        raw = data.code.strip().removeprefix("PARCELHUB:")
        hashed = fingerprint(raw, cfg.secret)
        with transaction(cfg) as db:
            row = db.execute(
                "SELECT id FROM parcels WHERE (otp_hash=? OR qr_hash=?) AND status='READY' AND code_expires_at>?",
                (hashed, hashed, int(time.time())),
            ).fetchone()
            svc.require(
                row is not None,
                "Kod tidak sah atau tamat tempoh. Dapatkan kod baharu di portal.",
                400,
            )
            p = svc.parcel(db, row["id"])
            svc.require(not p["maintenance"], "Loker memerlukan bantuan operator.")
            # Reissuing a kiosk session expires previous sessions for this parcel.
            db.execute(
                "DELETE FROM pickup_sessions WHERE parcel_id=? OR expires_at<=?",
                (p["id"], int(time.time())),
            )
            raw_session = token()
            expires = int(time.time()) + 600
            quote = svc.fees(p)
            db.execute(
                "INSERT INTO pickup_sessions VALUES (?,?,?,?,?)",
                (
                    fingerprint(raw_session, cfg.secret),
                    p["id"],
                    expires,
                    quote["total_cents"],
                    int(time.time()),
                ),
            )
            return {
                "token": raw_session,
                "expires_at": expires,
                "parcel": svc.serialize_parcel(p),
                "quote": quote,
            }

    @app.post("/api/kiosk/status")
    def kiosk_status(data: PickupToken):
        with transaction(cfg) as db:
            session, p = svc.pickup(db, data.token, cfg)
            c = db.execute(
                "SELECT id,state FROM commands WHERE parcel_id=? AND kind='PICKUP' ORDER BY created_at DESC,id DESC LIMIT 1",
                (p["id"],),
            ).fetchone()
            return {
                "parcel": svc.serialize_parcel(p),
                "due_cents": max(0, session["quote_cents"] - p["paid_cents"]),
                "command": dict(c) if c else None,
            }

    @app.post("/api/kiosk/payment")
    def payment(data: PickupToken):
        with transaction(cfg) as db:
            session, p = svc.pickup(db, data.token, cfg)
            svc.require(p["status"] == "READY", "Parcel tidak tersedia untuk bayaran.")
            due = max(0, session["quote_cents"] - p["paid_cents"])
            svc.require(due > 0, "Bayaran telah dijelaskan.")
            pay = svc.make_payment(db, p, due, "demo" if cfg.demo else "manual")
            return {"payment": pay, "demo": cfg.demo}

    @app.post("/api/kiosk/payment/{payment_id}/simulate")
    def pay_demo(payment_id: str, data: PickupToken):
        require_demo()
        with transaction(cfg) as db:
            session, p = svc.pickup(db, data.token, cfg)
            pay = db.execute(
                "SELECT * FROM payments WHERE id=? AND parcel_id=?",
                (payment_id, p["id"]),
            ).fetchone()
            svc.require(pay is not None, "Bayaran tidak dijumpai.", 404)
            svc.require(pay["method"] == "demo", "Kaedah bayaran tidak sah.", 403)
            svc.settle_payment(db, dict(pay), "demo-kiosk")
            return {"ok": True, "paid_cents": svc.parcel(db, p["id"])["paid_cents"]}

    @app.post("/api/kiosk/unlock")
    def unlock(data: PickupToken):
        with transaction(cfg) as db:
            session, p = svc.pickup(db, data.token, cfg)
            svc.require(
                p["status"] == "READY",
                "Pengambilan sedang diproses atau telah selesai.",
            )
            svc.require(
                p["paid_cents"] >= session["quote_cents"],
                "Selesaikan bayaran dahulu.",
                402,
            )
            cid = svc.command(db, p, "PICKUP", cfg, "kiosk")
            return {
                "command_id": cid,
                "parcel": svc.serialize_parcel(svc.parcel(db, p["id"])),
            }

    @app.post("/api/kiosk/close")
    def close_pickup(data: PickupClose):
        svc.require(
            cfg.hardware_mode == "simulated",
            "Pengesahan mesti datang daripada peranti.",
            403,
        )
        with transaction(cfg) as db:
            session, p = svc.pickup(db, data.token, cfg)
            c = db.execute(
                "SELECT id FROM commands WHERE parcel_id=? AND kind='PICKUP' AND state='opened'",
                (p["id"],),
            ).fetchone()
            svc.require(c is not None, "Pintu belum disahkan terbuka.")
            result = svc.door_event(
                db, c["id"], "closed", data.parcel_present, "demo-kiosk", cfg
            )
            return {"parcel": svc.serialize_parcel(result)}

    @app.get("/api/admin/payments")
    def staff_payments(req: Request):
        with transaction(cfg) as db:
            user(db, req, ("operator", "admin"))
            return {
                "payments": [
                    dict(r)
                    for r in db.execute(
                        """SELECT pay.*,p.tracking,u.name recipient_name FROM payments pay
                           JOIN parcels p ON p.id=pay.parcel_id JOIN users u ON u.id=p.recipient_id ORDER BY pay.created_at DESC LIMIT 200"""
                    )
                ]
            }

    @app.post("/api/admin/payments/{payment_id}/confirm")
    def confirm_cash(payment_id: str, req: Request):
        with transaction(cfg) as db:
            u = user(db, req, ("operator", "admin"))
            pay = db.execute(
                "SELECT * FROM payments WHERE id=?", (payment_id,)
            ).fetchone()
            svc.require(pay is not None, "Bayaran tidak dijumpai.", 404)
            svc.require(pay["method"] == "manual", "Bayaran ini bukan bayaran kaunter.")
            svc.settle_payment(db, dict(pay), u["id"])
            return {"ok": True}

    @app.post("/api/payments/webhook")
    async def webhook(req: Request):
        svc.require(
            len(cfg.payment_secret) >= 32, "Integrasi bayaran belum dikonfigurasi.", 503
        )
        timestamp = req.headers.get("x-payment-timestamp", "")
        try:
            svc.require(
                abs(int(time.time()) - int(timestamp)) <= 300,
                "Webhook telah tamat tempoh.",
                401,
            )
        except ValueError:
            raise HTTPException(401, "Tandatangan tidak sah.")
        body = await req.body()
        signature = hmac.new(
            cfg.payment_secret.encode(),
            timestamp.encode() + b"." + body,
            hashlib.sha256,
        ).hexdigest()
        svc.require(
            hmac.compare_digest(req.headers.get("x-payment-signature", ""), signature),
            "Tandatangan tidak sah.",
            401,
        )
        try:
            data = json.loads(body)
            event_id = data["event_id"]
            pid = data["payment_id"]
            amount = data["amount_cents"]
            svc.require(
                isinstance(event_id, str)
                and 1 <= len(event_id) <= 120
                and isinstance(pid, str)
                and type(amount) is int,
                "Data webhook tidak sah.",
                422,
            )
            svc.require(
                data.get("status") == "succeeded" and data.get("currency") == "MYR",
                "Status atau mata wang tidak sah.",
                422,
            )
        except (ValueError, KeyError, TypeError):
            raise HTTPException(422, "Data webhook tidak sah.")
        with transaction(cfg) as db:
            if db.execute(
                "SELECT 1 FROM payment_events WHERE event_id=?", (event_id,)
            ).fetchone():
                return {"ok": True, "duplicate": True}
            pay = db.execute("SELECT * FROM payments WHERE id=?", (pid,)).fetchone()
            svc.require(
                pay is not None and pay["amount_cents"] == amount,
                "Jumlah atau rujukan bayaran tidak sepadan.",
                409,
            )
            svc.settle_payment(db, dict(pay), "payment-provider")
            db.execute(
                "INSERT INTO payment_events VALUES (?,?)", (event_id, int(time.time()))
            )
            return {"ok": True}

    @app.get("/api/admin/overview")
    def overview(req: Request):
        with transaction(cfg) as db:
            user(db, req, ("operator", "admin"))
            now = datetime.now(ZoneInfo("Asia/Kuala_Lumpur"))
            midnight = int(
                now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
            )
            rows = [dict(r) for r in db.execute("SELECT * FROM parcels")]
            active = [p for p in rows if p["status"] in svc.ACTIVE]
            paid = db.execute(
                "SELECT COALESCE(SUM(amount_cents),0) amount FROM payments WHERE status='paid' AND settled_at>=?",
                (midnight,),
            ).fetchone()["amount"]
            measured = [
                p["pickup_seconds"] for p in rows if p["pickup_seconds"] is not None
            ]
            trend = []
            for offset in range(6, -1, -1):
                day = now - timedelta(days=offset)
                start = int(
                    day.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
                )
                end = start + 86400
                trend.append(
                    {
                        "day": day.strftime("%d/%m"),
                        "deposited": sum(
                            start <= (p["deposited_at"] or 0) < end for p in rows
                        ),
                        "collected": sum(
                            start <= (p["collected_at"] or 0) < end for p in rows
                        ),
                    }
                )
            return {
                "active": len(active),
                "overdue": sum(svc.fees(p)["overdue"] for p in active),
                "collected_today": sum(
                    (p["collected_at"] or 0) >= midnight for p in rows
                ),
                "revenue_today_cents": paid,
                "average_pickup_seconds": (
                    round(sum(measured) / len(measured), 1) if measured else None
                ),
                "measurement_count": len(measured),
                "trend": trend,
                "activity": [
                    dict(r)
                    for r in db.execute("SELECT * FROM audit ORDER BY id DESC LIMIT 30")
                ],
            }

    @app.patch("/api/admin/lockers/{locker_id}")
    def maintenance(locker_id: str, data: Maintain, req: Request):
        with transaction(cfg) as db:
            u = user(db, req, ("admin",))
            l = db.execute("SELECT * FROM lockers WHERE id=?", (locker_id,)).fetchone()
            svc.require(l is not None, "Loker tidak dijumpai.", 404)
            svc.require(not l["door_open"], "Pintu perlu ditutup sebelum menukar mod.")
            active = db.execute(
                "SELECT 1 FROM parcels WHERE locker_id=? AND status NOT IN ('COLLECTED','CANCELLED')",
                (locker_id,),
            ).fetchone()
            svc.require(
                not active, "Uruskan parcel aktif dahulu sebelum penyelenggaraan."
            )
            db.execute(
                "UPDATE lockers SET maintenance=? WHERE id=?",
                (int(data.enabled), locker_id),
            )
            svc.audit(
                db, u["id"], "MAINTENANCE_CHANGED", detail=f"{locker_id}: {data.reason}"
            )
            return {"ok": True}

    @app.post("/api/admin/parcels/{pid}/remind")
    def remind(pid: str, req: Request):
        with transaction(cfg) as db:
            u = user(db, req, ("operator", "admin"))
            p = svc.parcel(db, pid)
            svc.require(p["status"] == "READY", "Parcel tidak sedia untuk pengambilan.")
            recent = db.execute(
                "SELECT 1 FROM notifications WHERE parcel_id=? AND title='Peringatan pengambilan' AND created_at>?",
                (pid, int(time.time()) - 3600),
            ).fetchone()
            svc.require(
                not recent, "Peringatan sudah dihantar dalam sejam terakhir.", 429
            )
            svc.notify(
                db,
                p["recipient_id"],
                pid,
                "Peringatan pengambilan",
                f"Parcel anda berada di loker {p['locker_id']}. Baki caj semasa RM{svc.fees(p)['due_cents']/100:.2f}.",
            )
            svc.audit(db, u["id"], "IN_APP_REMINDER", pid)
            return {"ok": True, "channel": "in-app"}

    @app.post("/api/admin/parcels/{pid}/resolve")
    def resolve(pid: str, data: Resolve, req: Request):
        with transaction(cfg) as db:
            u = user(db, req, ("admin",))
            p = svc.parcel(db, pid)
            svc.require(
                p["status"] in ("ISSUE", "UNLOCK_PENDING", "PICKUP_OPEN", "RESERVED"),
                "Tiada insiden aktif untuk diselesaikan.",
            )
            svc.require(
                data.door_closed_confirmed,
                "Sahkan pemeriksaan fizikal dan pintu telah ditutup.",
                400,
            )
            if data.outcome == "restore":
                svc.require(
                    p["deposited_at"] is not None,
                    "Deposit belum selesai. Gunakan batal dan daftar semula.",
                )
                status = "READY"
            elif data.outcome == "collected":
                svc.require(p["deposited_at"] is not None, "Parcel belum disimpan.")
                status = "COLLECTED"
            else:
                svc.require(
                    not p["paid_cents"],
                    "Parcel berbayar memerlukan rekonsiliasi sebelum pembatalan.",
                )
                status = "CANCELLED"
            now = int(time.time())
            db.execute(
                "UPDATE commands SET state='fault',completed_at=? WHERE parcel_id=? AND state IN ('queued','opened')",
                (now, pid),
            )
            db.execute(
                "UPDATE lockers SET door_open=0,maintenance=? WHERE id=?",
                (0 if status == "READY" else 1, p["locker_id"]),
            )
            db.execute(
                "UPDATE parcels SET status=?,problem=?,collected_at=?,otp_hash=NULL,qr_hash=NULL WHERE id=?",
                (status, data.reason, now if status == "COLLECTED" else None, pid),
            )
            db.execute("DELETE FROM pickup_sessions WHERE parcel_id=?", (pid,))
            if status == "READY":
                svc.generate_code(db, svc.parcel(db, pid), cfg)
            svc.audit(db, u["id"], "MANUAL_RECOVERY", pid, f"{status}: {data.reason}")
            svc.notify(
                db,
                p["recipient_id"],
                pid,
                "Kemas kini daripada operator",
                f"Status parcel {p['tracking']}: {status}. {data.reason}",
            )
            return {"ok": True}

    @app.get("/api/admin/users")
    def users(req: Request):
        with transaction(cfg) as db:
            user(db, req, ("admin",))
            return {
                "users": [
                    dict(r)
                    for r in db.execute(
                        "SELECT id,name,email,student_id,role,created_at FROM users ORDER BY id DESC LIMIT 1000"
                    )
                ]
            }

    @app.post("/api/admin/users", status_code=201)
    def create_user(data: NewUser, req: Request):
        with transaction(cfg) as db:
            u = user(db, req, ("admin",))
            uid = db.execute(
                "INSERT INTO users(name,email,student_id,password,role,created_at) VALUES (?,?,?,?,?,?)",
                (
                    data.name.strip(),
                    data.email,
                    data.student_id.upper(),
                    password_hash(data.password),
                    data.role,
                    int(time.time()),
                ),
            ).lastrowid
            svc.audit(db, u["id"], "USER_CREATED", detail=f"{uid} ({data.role})")
            return {"id": uid}

    @app.get("/api/admin/export.csv")
    def export(req: Request):
        with transaction(cfg) as db:
            user(db, req, ("admin",))
            rows = db.execute(
                "SELECT id,tracking,locker_id,courier,status,deposited_at,collected_at,paid_cents FROM parcels ORDER BY created_at DESC"
            ).fetchall()
            out = io.StringIO()
            writer = csv.writer(out)
            writer.writerow(
                [
                    "ID",
                    "Tracking",
                    "Locker",
                    "Courier",
                    "Status",
                    "Deposited (UTC epoch)",
                    "Collected (UTC epoch)",
                    "Paid (MYR)",
                ]
            )

            def safe(v):
                text = str(v or "")
                return (
                    "'" + text
                    if text.startswith(("=", "+", "-", "@", "\t", "\r"))
                    else text
                )

            for r in rows:
                writer.writerow(
                    [safe(v) for v in list(r)[:-1]] + [f'{r["paid_cents"]/100:.2f}']
                )
            return Response(
                out.getvalue(),
                media_type="text/csv",
                headers={
                    "Content-Disposition": 'attachment; filename="parcelhub-parcels.csv"'
                },
            )

    @app.get("/api/device/commands")
    def commands(req: Request):
        device_auth(req)
        with transaction(cfg) as db:
            return {
                "station_id": "PAP-01",
                "commands": [
                    dict(r)
                    for r in db.execute(
                        "SELECT id,parcel_id,locker_id,kind,state,created_at FROM commands WHERE state IN ('queued','opened') ORDER BY created_at LIMIT 16"
                    )
                ],
            }

    @app.post("/api/device/commands/{cid}/events")
    def device_event(cid: str, data: DeviceEvent, req: Request):
        device_auth(req)
        svc.require(cfg.hardware_mode == "device", "Mod peranti belum diaktifkan.", 409)
        with transaction(cfg) as db:
            p = svc.door_event(
                db,
                cid,
                data.event,
                data.parcel_present,
                "device:PAP-01",
                cfg,
                data.detail,
            )
            return {"ok": True, "status": p["status"]}

    app.mount("/static", StaticFiles(directory=STATIC), name="static")

    @app.get("/")
    def index():
        return FileResponse(
            STATIC / "index.html", headers={"Cache-Control": "no-cache"}
        )

    return app
