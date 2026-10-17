"""Shared, transactional order workflow for the web portal and Telegram bot."""

import re
import secrets
import time
from . import service as svc

LABELS = {
    "PENDING": "Menunggu pekerja",
    "ACCEPTED": "Diterima pekerja",
    "RESERVED": "Sedang disimpan",
    "READY": "Sedia diambil",
    "UNLOCK_PENDING": "Menunggu pintu",
    "PICKUP_OPEN": "Pintu terbuka",
    "COLLECTED": "Selesai diambil",
    "ISSUE": "Perlu bantuan",
    "CANCELLED": "Dibatalkan",
    "REJECTED": "Ditolak",
}


def get(db, oid, user):
    row = db.execute(
        """SELECT o.*,u.name recipient_name,u.student_id,a.name assigned_name
        FROM orders o JOIN users u ON u.id=o.recipient_id
        LEFT JOIN users a ON a.id=o.assigned_to WHERE o.id=?""",
        (oid,),
    ).fetchone()
    svc.require(row is not None, "Order tidak dijumpai.", 404)
    svc.require(
        user["role"] != "recipient" or row["recipient_id"] == user["id"],
        "Order tidak dijumpai.",
        404,
    )
    return dict(row)


def serialize(db, order, user, cfg):
    result = dict(order)
    result["pickup_code"] = None
    result["parcel"] = None
    if order["parcel_id"]:
        p = svc.parcel(db, order["parcel_id"])
        result["parcel"] = svc.serialize_parcel(p, user["role"] != "recipient")
        if order["status"] == "FULFILLING":
            result["status"] = p["status"]
        if user["id"] == order["recipient_id"]:
            code = svc.current_code(db, p, cfg)
            if code:
                result["pickup_code"] = {
                    "otp": code["otp"],
                    "expires_at": code["expires_at"],
                }
    result["status_label"] = LABELS.get(result["status"], result["status"])
    return result


def listing(db, user, cfg):
    ids = db.execute(
        "SELECT o.id FROM orders o LEFT JOIN parcels p ON p.id=o.parcel_id WHERE (?!='recipient' OR o.recipient_id=?) ORDER BY CASE WHEN o.status='PENDING' THEN 0 WHEN o.status='ACCEPTED' THEN 1 WHEN p.status IN ('RESERVED','ISSUE') THEN 2 ELSE 3 END,o.created_at DESC,o.rowid DESC LIMIT 200",
        (user["role"], user["id"]),
    ).fetchall()
    return [serialize(db, get(db, row["id"], user), user, cfg) for row in ids]


def create(db, user, data, source="web"):
    svc.require(
        user["role"] == "recipient",
        "Order baharu perlu dibuat melalui akaun pelanggan.",
        403,
    )
    tracking = str(data.get("tracking", "")).strip().upper()
    courier = str(data.get("courier", "")).strip()
    size = str(data.get("size", "M")).strip().upper()
    notes = str(data.get("notes", "")).strip()
    svc.require(
        bool(re.fullmatch(r"[A-Z0-9-]{4,60}", tracking)),
        "Tracking mesti 4–60 huruf, angka atau sengkang.",
        422,
    )
    svc.require(
        2 <= len(courier) <= 50 and not any(ord(c) < 32 for c in courier),
        "Nama kurier mesti 2–50 aksara.",
        422,
    )
    svc.require(size in ("S", "M", "L", "XL"), "Pilih saiz S, M, L atau XL.", 422)
    svc.require(len(notes) <= 300, "Catatan maksimum 300 aksara.", 422)
    existing = db.execute(
        "SELECT * FROM orders WHERE tracking=? AND status NOT IN ('CANCELLED','REJECTED')",
        (tracking,),
    ).fetchone()
    if existing:
        svc.require(
            existing["recipient_id"] == user["id"]
            and existing["courier"] == courier
            and existing["size"] == size
            and existing["notes"] == notes,
            "Tracking ini sudah mempunyai order. Semak order anda atau hubungi PAP.",
        )
        return get(
            db, existing["id"], user
        )  # retried submit, no duplicate notifications
    svc.require(
        not db.execute(
            "SELECT 1 FROM parcels WHERE tracking=?", (tracking,)
        ).fetchone(),
        "Tracking ini sudah didaftarkan. Semak Parcel saya atau hubungi PAP.",
    )
    count = db.execute(
        "SELECT COUNT(*) FROM orders WHERE recipient_id=? AND status IN ('PENDING','ACCEPTED')",
        (user["id"],),
    ).fetchone()[0]
    svc.require(
        count < 20,
        "Maksimum 20 order menunggu. Selesaikan order terdahulu dahulu.",
        429,
    )
    oid = "ORD-" + secrets.token_hex(4).upper()
    now = int(time.time())
    db.execute(
        "INSERT INTO orders(id,recipient_id,tracking,courier,size,notes,source,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (oid, user["id"], tracking, courier, size, notes, source, now, now),
    )
    svc.notify(
        db,
        user["id"],
        oid,
        "Order diterima",
        f"{oid} · {tracking}. Pekerja PAP akan memproses permintaan simpanan anda. Kod pengambilan akan diberi selepas parcel disimpan.",
    )
    for staff in db.execute(
        "SELECT id FROM users WHERE role IN ('operator','admin')"
    ).fetchall():
        svc.notify(
            db,
            staff["id"],
            oid,
            "Order baharu untuk diproses",
            f"{oid}\n{user['name']} · {user['student_id']}\n{courier} · {tracking} · Saiz {size}\nBuka Tugasan di web atau /accept {oid} dalam bot.",
        )
    svc.audit(db, user["id"], "ORDER_CREATED", detail=f"{oid} | {source}")
    return get(db, oid, user)


def accept(db, oid, user):
    svc.require(
        user["role"] in ("operator", "admin"), "Tindakan ini untuk pekerja.", 403
    )
    order = get(db, oid, user)
    if order["status"] == "ACCEPTED" and order["assigned_to"] == user["id"]:
        return order
    svc.require(
        order["status"] == "PENDING",
        "Order telah diambil pekerja lain atau sudah diproses.",
    )
    db.execute(
        "UPDATE orders SET status='ACCEPTED',assigned_to=?,updated_at=? WHERE id=?",
        (user["id"], int(time.time()), oid),
    )
    svc.notify(
        db,
        order["recipient_id"],
        oid,
        "Order sedang diproses",
        f"{oid}: {user['name']} menerima tugasan anda. Tunggu notifikasi sedia diambil sebelum ke loker.",
    )
    svc.audit(db, user["id"], "ORDER_ACCEPTED", detail=oid)
    return get(db, oid, user)


def cancel(db, oid, user, reason=""):
    order = get(db, oid, user)
    if user["role"] == "recipient":
        svc.require(
            order["status"] == "PENDING",
            "Order sudah diterima pekerja. Hubungi PAP untuk perubahan.",
        )
        status = "CANCELLED"
        reason = "Dibatalkan oleh pelanggan."
    else:
        svc.require(
            order["status"] in ("PENDING", "ACCEPTED"),
            "Order ini sudah dalam proses simpanan.",
        )
        svc.require(
            order["assigned_to"] in (None, user["id"]),
            "Order ini di bawah pekerja lain.",
        )
        svc.require(
            5 <= len(reason.strip()) <= 300,
            "Nyatakan sebab penolakan (5–300 aksara).",
            422,
        )
        status = "REJECTED"
    db.execute(
        "UPDATE orders SET status=?,reason=?,updated_at=? WHERE id=?",
        (status, reason, int(time.time()), oid),
    )
    svc.notify(
        db,
        order["recipient_id"],
        oid,
        "Kemas kini order",
        f"{oid}: {LABELS[status]}. {reason}",
    )
    if user["role"] == "recipient":
        for staff in db.execute(
            "SELECT id FROM users WHERE role IN ('operator','admin')"
        ).fetchall():
            svc.notify(
                db,
                staff["id"],
                oid,
                "Order dibatalkan",
                f"{oid} · {order['tracking']} dibatalkan oleh pelanggan.",
            )
    svc.audit(db, user["id"], "ORDER_" + status, detail=oid)
    return get(db, oid, user)


def store(db, oid, user, cfg, size=None, locker_id=None):
    svc.require(
        user["role"] in ("operator", "admin"), "Tindakan ini untuk pekerja.", 403
    )
    order = get(db, oid, user)
    svc.require(
        order["assigned_to"] == user["id"],
        "Terima tugasan ini dahulu; hanya pekerja yang ditugaskan boleh menyimpannya.",
    )
    if order["status"] == "FULFILLING" and order["parcel_id"]:
        p = svc.parcel(db, order["parcel_id"])
        svc.require(
            p["status"] in ("RESERVED", "READY"),
            "Order sudah selesai atau memerlukan bantuan.",
        )
        return serialize(db, order, user, cfg)
    svc.require(
        order["status"] == "ACCEPTED", "Order belum diterima atau telah selesai."
    )
    size = size or order["size"]
    svc.require(size in ("S", "M", "L", "XL"), "Saiz loker tidak sah.", 422)
    locker = db.execute(
        """SELECT l.* FROM lockers l WHERE l.size=? AND l.maintenance=0 AND l.door_open=0
        AND (? IS NULL OR l.id=?) AND NOT EXISTS (SELECT 1 FROM parcels p WHERE p.locker_id=l.id AND p.status NOT IN ('COLLECTED','CANCELLED'))
        ORDER BY l.id LIMIT 1""",
        (size, locker_id, locker_id),
    ).fetchone()
    svc.require(
        locker is not None,
        "Tiada loker saiz ini tersedia. Pilih saiz lain di web atau cuba kemudian.",
    )
    pid = order["parcel_id"] or "PH-" + secrets.token_hex(4).upper()
    if order["parcel_id"]:
        p = svc.parcel(db, pid)
        svc.require(
            p["status"] == "CANCELLED"
            and not p["paid_cents"]
            and not p["deposited_at"],
            "Deposit terdahulu perlu diperiksa oleh admin.",
        )
        db.execute(
            "UPDATE parcels SET status='RESERVED',locker_id=?,fee_cents=?,problem='',otp_hash=NULL,qr_hash=NULL WHERE id=?",
            (locker["id"], locker["fee_cents"], pid),
        )
    else:
        db.execute(
            "INSERT INTO parcels(id,tracking,recipient_id,locker_id,courier,status,created_at,fee_cents) VALUES (?,?,?,?,?,'RESERVED',?,?)",
            (
                pid,
                order["tracking"],
                order["recipient_id"],
                locker["id"],
                order["courier"],
                int(time.time()),
                locker["fee_cents"],
            ),
        )
    db.execute(
        "UPDATE orders SET status='FULFILLING',parcel_id=?,updated_at=? WHERE id=?",
        (pid, int(time.time()), oid),
    )
    svc.command(db, svc.parcel(db, pid), "DEPOSIT", cfg, user["id"])
    svc.audit(db, user["id"], "ORDER_STORE_STARTED", pid, oid)
    return serialize(db, get(db, oid, user), user, cfg)


def confirm_storage(db, oid, user, cfg):
    svc.require(
        user["role"] in ("operator", "admin"), "Tindakan ini untuk pekerja.", 403
    )
    svc.require(
        cfg.hardware_mode == "simulated",
        "Pengesahan simpanan mesti datang daripada sensor peranti.",
        403,
    )
    order = get(db, oid, user)
    svc.require(order["assigned_to"] == user["id"], "Order ini di bawah pekerja lain.")
    svc.require(
        order["status"] == "FULFILLING" and order["parcel_id"],
        "Mulakan simpanan dahulu.",
    )
    p = svc.parcel(db, order["parcel_id"])
    if p["status"] == "READY":
        return serialize(db, order, user, cfg)
    svc.require(p["status"] == "RESERVED", "Parcel bukan dalam proses simpanan.")
    command = db.execute(
        "SELECT id FROM commands WHERE parcel_id=? AND kind='DEPOSIT' AND state='opened'",
        (p["id"],),
    ).fetchone()
    svc.require(command is not None, "Pintu belum disahkan terbuka.")
    svc.door_event(db, command["id"], "closed", True, str(user["id"]), cfg)
    return serialize(db, order, user, cfg)
