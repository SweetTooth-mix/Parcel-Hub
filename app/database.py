from contextlib import contextmanager
from pathlib import Path
import sqlite3
import time
from .security import password_hash, fingerprint


def connect(settings):
    db = sqlite3.connect(settings.database, timeout=15, isolation_level=None)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA busy_timeout=15000")
    return db


@contextmanager
def transaction(settings):
    db = connect(settings)
    try:
        db.execute("BEGIN IMMEDIATE")
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def initialize(settings):
    Path(settings.database).parent.mkdir(parents=True, exist_ok=True)
    db = connect(settings)
    db.execute("PRAGMA journal_mode=WAL")
    db.executescript(Path(__file__).with_name("schema.sql").read_text())
    db.close()
    with transaction(settings) as db:
        marker = db.execute(
            "SELECT value FROM settings WHERE key='demo_seeded'"
        ).fetchone()
        if not settings.demo and marker:
            raise RuntimeError(
                "A demo database cannot be used with DEMO_MODE=false. Use a fresh production DATA_DIR."
            )
        if not db.execute("SELECT 1 FROM lockers LIMIT 1").fetchone():
            for tower, count, sizes in [
                ("A", 8, ["S"] * 4 + ["M"] * 4),
                ("B", 4, ["L"] * 4),
                ("C", 4, ["XL"] * 4),
            ]:
                for i in range(count):
                    size = sizes[i]
                    db.execute(
                        "INSERT INTO lockers(id,size,fee_cents) VALUES (?,?,?)",
                        (f"{tower}{i+1:02}", size, 50 if size in ("S", "M") else 100),
                    )
        if not db.execute("SELECT 1 FROM users LIMIT 1").fetchone():
            if settings.demo:
                seed_demo(db, settings)
            elif settings.admin_email and len(settings.admin_password) >= 12:
                db.execute(
                    "INSERT INTO users(name,email,student_id,password,role,created_at) VALUES (?,?,?,?,?,?)",
                    (
                        "Pentadbir",
                        settings.admin_email.lower(),
                        "ADMIN-001",
                        password_hash(settings.admin_password),
                        "admin",
                        int(time.time()),
                    ),
                )
            else:
                raise RuntimeError(
                    "First non-demo start requires ADMIN_EMAIL and ADMIN_PASSWORD (12+ characters)."
                )


def seed_demo(db, settings):
    now = int(time.time())
    db.execute("INSERT OR REPLACE INTO settings VALUES ('demo_seeded','true')")
    users = [
        ("Aiman Hakim", "aiman@demo.parcelhub.test", "CA23019", "recipient"),
        ("Nur Izzah", "izzah@demo.parcelhub.test", "CA22041", "recipient"),
        ("Daniel Lee", "daniel@demo.parcelhub.test", "CB23110", "recipient"),
        ("Operator PAP", "operator@demo.parcelhub.test", "OP-001", "operator"),
        ("Admin ParcelHub", "admin@demo.parcelhub.test", "ADM-001", "admin"),
    ]
    for name, email, student, role in users:
        db.execute(
            "INSERT INTO users(name,email,student_id,password,role,created_at) VALUES (?,?,?,?,?,?)",
            (name, email, student, password_hash("ParcelDemo2026!"), role, now),
        )
    samples = [
        ("PH-DEMO01", "SPXMY04829104", 1, "A02", "SPX Express", 5, "482910", 50),
        ("PH-DEMO02", "JT6019283741", 1, "B01", "J&T Express", 29, "591028", 100),
        ("PH-DEMO03", "NVMY99201842", 2, "A06", "Ninja Van", 3, "739104", 50),
        ("PH-DEMO04", "ERC88291042MY", 3, "C02", "Pos Laju", 10, "820419", 100),
    ]
    for pid, tracking, uid, locker, courier, hours, otp, fee in samples:
        db.execute(
            """INSERT INTO parcels(id,tracking,recipient_id,locker_id,courier,status,created_at,deposited_at,
                      otp_hash,code_expires_at,fee_cents) VALUES (?,?,?,?,?,'READY',?,?,?,?,?)""",
            (
                pid,
                tracking,
                uid,
                locker,
                courier,
                now - hours * 3600,
                now - hours * 3600,
                fingerprint(otp, settings.secret),
                now + 72 * 3600,
                fee,
            ),
        )
        db.execute(
            "INSERT INTO notifications(user_id,parcel_id,title,body,created_at) VALUES (?,?,?,?,?)",
            (
                uid,
                pid,
                "Parcel sedia diambil",
                f"{courier}: parcel anda berada di loker {locker}, PAP. Dapatkan kod di portal anda.",
                now - hours * 3600,
            ),
        )
    db.execute("UPDATE lockers SET maintenance=1 WHERE id='C04'")
    db.execute(
        "INSERT INTO audit(actor,action,detail,created_at) VALUES ('system','DEMO_INITIALIZED','Data contoh; tiada mesej atau bayaran sebenar.',?)",
        (now,),
    )
