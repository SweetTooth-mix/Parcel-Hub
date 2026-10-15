PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE COLLATE NOCASE,
 student_id TEXT NOT NULL UNIQUE COLLATE NOCASE, password TEXT NOT NULL,
 role TEXT NOT NULL CHECK(role IN ('recipient','operator','admin')), created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
 token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), csrf TEXT NOT NULL,
 expires_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS lockers (
 id TEXT PRIMARY KEY, size TEXT NOT NULL, fee_cents INTEGER NOT NULL,
 maintenance INTEGER NOT NULL DEFAULT 0, door_open INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS parcels (
 id TEXT PRIMARY KEY, tracking TEXT NOT NULL UNIQUE COLLATE NOCASE,
 recipient_id INTEGER NOT NULL REFERENCES users(id), locker_id TEXT NOT NULL REFERENCES lockers(id),
 courier TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('RESERVED','READY','UNLOCK_PENDING','PICKUP_OPEN','COLLECTED','ISSUE','CANCELLED')),
 created_at INTEGER NOT NULL, deposited_at INTEGER, collected_at INTEGER,
 otp_hash TEXT, qr_hash TEXT, code_expires_at INTEGER,
 fee_cents INTEGER NOT NULL, paid_cents INTEGER NOT NULL DEFAULT 0,
 unlock_started_at INTEGER, pickup_seconds INTEGER, problem TEXT NOT NULL DEFAULT ''
);
CREATE UNIQUE INDEX IF NOT EXISTS active_locker ON parcels(locker_id)
 WHERE status NOT IN ('COLLECTED','CANCELLED');
CREATE UNIQUE INDEX IF NOT EXISTS active_otp ON parcels(otp_hash) WHERE otp_hash IS NOT NULL;
CREATE TABLE IF NOT EXISTS pickup_sessions (
 token_hash TEXT PRIMARY KEY, parcel_id TEXT NOT NULL REFERENCES parcels(id),
 expires_at INTEGER NOT NULL, quote_cents INTEGER NOT NULL, verified_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS payments (
 id TEXT PRIMARY KEY, parcel_id TEXT NOT NULL REFERENCES parcels(id),
 amount_cents INTEGER NOT NULL CHECK(amount_cents >= 0), status TEXT NOT NULL DEFAULT 'pending',
 method TEXT NOT NULL, created_at INTEGER NOT NULL, settled_at INTEGER, expires_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS payment_events (event_id TEXT PRIMARY KEY, created_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS commands (
 id TEXT PRIMARY KEY, parcel_id TEXT NOT NULL REFERENCES parcels(id), locker_id TEXT NOT NULL REFERENCES lockers(id),
 kind TEXT NOT NULL CHECK(kind IN ('DEPOSIT','PICKUP')), state TEXT NOT NULL DEFAULT 'queued',
 created_at INTEGER NOT NULL, acknowledged_at INTEGER, completed_at INTEGER
);
CREATE UNIQUE INDEX IF NOT EXISTS pending_command ON commands(locker_id) WHERE state IN ('queued','opened');
CREATE TABLE IF NOT EXISTS notifications (
 id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), parcel_id TEXT,
 title TEXT NOT NULL, body TEXT NOT NULL, created_at INTEGER NOT NULL, read_at INTEGER
);
CREATE TABLE IF NOT EXISTS audit (
 id INTEGER PRIMARY KEY, actor TEXT NOT NULL, action TEXT NOT NULL, parcel_id TEXT,
 detail TEXT NOT NULL DEFAULT '', created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS rate_limits (key TEXT PRIMARY KEY, count INTEGER NOT NULL, expires_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
PRAGMA user_version=1;
