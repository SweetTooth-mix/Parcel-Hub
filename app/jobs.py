"""Local housekeeping: in-app reminders, expired sessions and stalled device commands."""

import time
from .database import transaction
from . import service as svc


def housekeeping(settings):
    now = int(time.time())
    with transaction(settings) as db:
        db.execute("DELETE FROM sessions WHERE expires_at<=?", (now,))
        db.execute("DELETE FROM pickup_sessions WHERE expires_at<=?", (now,))
        db.execute("DELETE FROM rate_limits WHERE expires_at<=?", (now,))
        db.execute(
            "UPDATE payments SET status='expired' WHERE status='pending' AND expires_at<=?",
            (now,),
        )
        for row in db.execute(
            "SELECT id,recipient_id,locker_id FROM parcels WHERE status='READY' AND deposited_at<?",
            (now - 86400,),
        ).fetchall():
            recent = db.execute(
                "SELECT 1 FROM audit WHERE parcel_id=? AND action='AUTO_REMINDER' AND created_at>?",
                (row["id"], now - 12 * 3600),
            ).fetchone()
            if not recent:
                svc.notify(
                    db,
                    row["recipient_id"],
                    row["id"],
                    "Peringatan parcel lewat",
                    f"Parcel di loker {row['locker_id']} sudah melebihi 24 jam. Semak caj semasa dan kod pengambilan di portal.",
                )
                svc.audit(
                    db,
                    "system",
                    "AUTO_REMINDER",
                    row["id"],
                    "In-app; sela minimum 12 jam.",
                )
        if settings.hardware_mode == "device":
            stalled = db.execute(
                "SELECT id FROM commands WHERE state='queued' AND created_at<?",
                (now - 90,),
            ).fetchall()
            for row in stalled:
                svc.door_event(
                    db,
                    row["id"],
                    "fault",
                    None,
                    "system",
                    settings,
                    "Tiada pengesahan pintu selepas 90 saat. Periksa peranti sebelum pemulihan.",
                )
