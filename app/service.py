"""Transactional locker workflow. All callers supply an active database transaction."""

import math
import secrets
import time
from fastapi import HTTPException
from .security import fingerprint, token

ACTIVE = ("RESERVED", "READY", "UNLOCK_PENDING", "PICKUP_OPEN", "ISSUE")


def require(condition, detail, code=409):
    if not condition:
        raise HTTPException(code, detail)


def audit(db, actor, action, parcel_id=None, detail=""):
    db.execute(
        "INSERT INTO audit(actor,action,parcel_id,detail,created_at) VALUES (?,?,?,?,?)",
        (str(actor), action, parcel_id, detail, int(time.time())),
    )


def notify(db, uid, pid, title, body):
    db.execute(
        "INSERT INTO notifications(user_id,parcel_id,title,body,created_at) VALUES (?,?,?,?,?)",
        (uid, pid, title, body, int(time.time())),
    )


def parcel(db, pid):
    row = db.execute(
        """SELECT p.*,u.name recipient_name,u.email recipient_email,u.student_id,l.size,
                        l.maintenance,l.door_open FROM parcels p JOIN users u ON u.id=p.recipient_id
                        JOIN lockers l ON l.id=p.locker_id WHERE p.id=?""",
        (pid,),
    ).fetchone()
    require(row is not None, "Parcel tidak dijumpai.", 404)
    return dict(row)


def fees(p, now=None):
    now = now or int(time.time())
    end = p.get("collected_at") or now
    elapsed = max(0, end - (p.get("deposited_at") or now))
    blocks = math.ceil(max(0, elapsed - 86400) / 21600)
    total = p["fee_cents"] + blocks * 100
    return {
        "base_cents": p["fee_cents"],
        "late_cents": blocks * 100,
        "late_blocks": blocks,
        "total_cents": total,
        "due_cents": max(0, total - p["paid_cents"]),
        "deadline": p["deposited_at"] + 86400 if p.get("deposited_at") else None,
        "overdue": elapsed > 86400 and p["status"] not in ("COLLECTED", "CANCELLED"),
    }


def serialize_parcel(p, staff=False):
    fields = [
        "id",
        "tracking",
        "locker_id",
        "courier",
        "status",
        "created_at",
        "deposited_at",
        "collected_at",
        "fee_cents",
        "paid_cents",
        "size",
        "problem",
        "pickup_seconds",
        "code_expires_at",
        "door_open",
    ]
    if staff:
        fields += ["recipient_id", "recipient_name", "recipient_email", "student_id"]
    result = {k: p.get(k) for k in fields}
    result["fees"] = fees(p)
    return result


def generate_code(db, p, settings):
    require(
        p["status"] == "READY", "Kod hanya boleh dijana untuk parcel sedia diambil."
    )
    for _ in range(30):
        code = str(secrets.randbelow(900000) + 100000)
        hashed = fingerprint(code, settings.secret)
        if not db.execute(
            "SELECT 1 FROM parcels WHERE otp_hash=?", (hashed,)
        ).fetchone():
            break
    else:
        raise HTTPException(503, "Kod tidak dapat dijana. Cuba sebentar lagi.")
    qr = token()
    expires = int(time.time()) + 72 * 3600
    db.execute(
        "UPDATE parcels SET otp_hash=?,qr_hash=?,code_expires_at=? WHERE id=?",
        (hashed, fingerprint(qr, settings.secret), expires, p["id"]),
    )
    db.execute("DELETE FROM pickup_sessions WHERE parcel_id=?", (p["id"],))
    return {"otp": code, "qr_token": qr, "expires_at": expires}


def pickup(db, raw, settings):
    row = db.execute(
        "SELECT * FROM pickup_sessions WHERE token_hash=?",
        (fingerprint(raw, settings.secret),),
    ).fetchone()
    require(
        row is not None and row["expires_at"] > time.time(),
        "Sesi pengambilan tamat. Sahkan kod semula.",
        401,
    )
    return dict(row), parcel(db, row["parcel_id"])


def make_payment(db, p, amount, method):
    now = int(time.time())
    db.execute(
        "UPDATE payments SET status='expired' WHERE parcel_id=? AND status='pending' AND expires_at<=?",
        (p["id"], now),
    )
    existing = db.execute(
        "SELECT * FROM payments WHERE parcel_id=? AND status='pending' AND amount_cents=? AND method=? AND expires_at>?",
        (p["id"], amount, method, now),
    ).fetchone()
    if existing:
        return dict(existing)
    pid = "PAY-" + secrets.token_hex(6).upper()
    db.execute(
        "INSERT INTO payments(id,parcel_id,amount_cents,method,created_at,expires_at) VALUES (?,?,?,?,?,?)",
        (pid, p["id"], amount, method, now, now + 600),
    )
    return dict(db.execute("SELECT * FROM payments WHERE id=?", (pid,)).fetchone())


def settle_payment(db, pay, actor):
    if pay["status"] == "paid":
        return
    require(
        pay["status"] == "pending" and pay["expires_at"] > time.time(),
        "Permintaan bayaran telah tamat.",
    )
    p = parcel(db, pay["parcel_id"])
    require(p["status"] == "READY", "Parcel tidak tersedia untuk bayaran.")
    db.execute(
        "UPDATE payments SET status='paid',settled_at=? WHERE id=?",
        (int(time.time()), pay["id"]),
    )
    db.execute(
        "UPDATE parcels SET paid_cents=paid_cents+? WHERE id=?",
        (pay["amount_cents"], p["id"]),
    )
    # Retire other outstanding intents; a second gateway event must never charge the same quote again.
    db.execute(
        "UPDATE payments SET status='cancelled' WHERE parcel_id=? AND status='pending' AND id<>?",
        (p["id"], pay["id"]),
    )
    audit(
        db,
        actor,
        "PAYMENT_SETTLED",
        p["id"],
        f"{pay['id']} | {pay['method']} | {pay['amount_cents']} sen",
    )


def command(db, p, kind, settings, actor):
    require(not p["maintenance"], "Loker dalam penyelenggaraan. Sila hubungi operator.")
    require(not p["door_open"], "Pintu masih terbuka. Tutup pintu dahulu.")
    require(
        not db.execute(
            "SELECT 1 FROM commands WHERE locker_id=? AND state IN ('queued','opened')",
            (p["locker_id"],),
        ).fetchone(),
        "Arahan loker masih diproses.",
    )
    cid = "CMD-" + secrets.token_hex(6).upper()
    now = int(time.time())
    db.execute(
        "INSERT INTO commands(id,parcel_id,locker_id,kind,created_at) VALUES (?,?,?,?,?)",
        (cid, p["id"], p["locker_id"], kind, now),
    )
    if kind == "PICKUP":
        db.execute(
            "UPDATE parcels SET status='UNLOCK_PENDING',unlock_started_at=? WHERE id=?",
            (now, p["id"]),
        )
    audit(db, actor, kind + "_REQUESTED", p["id"], p["locker_id"])
    if settings.hardware_mode == "simulated":
        door_event(db, cid, "opened", None, "simulator", settings)
    return cid


def door_event(db, cid, event, parcel_present, actor, settings, detail=""):
    row = db.execute("SELECT * FROM commands WHERE id=?", (cid,)).fetchone()
    require(row is not None, "Arahan tidak dijumpai.", 404)
    c = dict(row)
    if c["state"] == "closed" and event == "closed":
        return parcel(db, c["parcel_id"])
    require(c["state"] not in ("closed", "fault"), "Arahan telah selesai.")
    p = parcel(db, c["parcel_id"])
    now = int(time.time())
    if event == "opened":
        if c["state"] == "opened":
            return p
        db.execute(
            "UPDATE commands SET state='opened',acknowledged_at=? WHERE id=?",
            (now, cid),
        )
        db.execute("UPDATE lockers SET door_open=1 WHERE id=?", (c["locker_id"],))
        if c["kind"] == "PICKUP":
            db.execute("UPDATE parcels SET status='PICKUP_OPEN' WHERE id=?", (p["id"],))
    elif event == "closed":
        require(c["state"] == "opened", "Pengesahan pintu terbuka diperlukan dahulu.")
        require(
            parcel_present is not None,
            "Sahkan sama ada parcel masih di dalam loker.",
            422,
        )
        db.execute(
            "UPDATE commands SET state='closed',completed_at=? WHERE id=?", (now, cid)
        )
        db.execute("UPDATE lockers SET door_open=0 WHERE id=?", (c["locker_id"],))
        if c["kind"] == "DEPOSIT":
            if parcel_present:
                db.execute(
                    "UPDATE parcels SET status='READY',deposited_at=? WHERE id=?",
                    (now, p["id"]),
                )
                generate_code(db, parcel(db, p["id"]), settings)
                notify(
                    db,
                    p["recipient_id"],
                    p["id"],
                    "Parcel sedia diambil",
                    f"{p['courier']}: ambil parcel di loker {p['locker_id']}, PAP. Dapatkan kod di portal. Tempoh asas 24 jam.",
                )
            else:
                db.execute(
                    "UPDATE parcels SET status='CANCELLED' WHERE id=?", (p["id"],)
                )
        elif not parcel_present:
            seconds = max(0, now - (p["unlock_started_at"] or now))
            db.execute(
                "UPDATE parcels SET status='COLLECTED',collected_at=?,pickup_seconds=?,otp_hash=NULL,qr_hash=NULL WHERE id=?",
                (now, seconds, p["id"]),
            )
            notify(
                db,
                p["recipient_id"],
                p["id"],
                "Pengambilan selesai",
                f"Parcel {p['tracking']} telah diambil. Jumlah bayaran RM{p['paid_cents']/100:.2f}. Terima kasih.",
            )
        else:
            db.execute("UPDATE parcels SET status='READY' WHERE id=?", (p["id"],))
    elif event == "fault":
        require(bool(detail.strip()), "Nyatakan masalah pintu.", 422)
        db.execute(
            "UPDATE commands SET state='fault',completed_at=? WHERE id=?", (now, cid)
        )
        db.execute("UPDATE lockers SET maintenance=1 WHERE id=?", (c["locker_id"],))
        db.execute(
            "UPDATE parcels SET status='ISSUE',problem=? WHERE id=?",
            (detail[:300], p["id"]),
        )
        notify(
            db,
            p["recipient_id"],
            p["id"],
            "Bantuan operator diperlukan",
            f"Loker {p['locker_id']} memerlukan pemeriksaan. Sila hubungi kaunter PAP.",
        )
    audit(db, actor, "DOOR_" + event.upper(), p["id"], detail or c["locker_id"])
    return parcel(db, p["id"])
