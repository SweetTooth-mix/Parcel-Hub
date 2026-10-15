# Operation and deployment

## Local demo

`docker compose up --build` binds to `127.0.0.1:8000`. It seeds only an empty database. Restarting the service preserves users, parcels, session records and payments in the named volume.

The native Python process reads environment variables, not `.env` automatically. Docker Compose reads `.env`. For native operation, export the relevant values in the process environment or configure them in your service manager.

## Non-demo pilot

Use a **fresh DATA_DIR/volume**. A demo-seeded database is explicitly rejected with `DEMO_MODE=false`, preventing known demo accounts from being carried into an operational deployment.

Required configuration:

| Variable | Setting |
| --- | --- |
| `APP_ENV` | `production` |
| `DEMO_MODE` | `false` |
| `APP_SECRET` | Random secret of at least 32 characters; retain across restarts |
| `APP_ORIGIN` | Exact HTTPS frontend origin, without a path |
| `HARDWARE_MODE` | `device` |
| `DEVICE_TOKEN` | Separate random secret of at least 32 characters |
| `ADMIN_EMAIL` | Bootstrap admin e-mail on first start |
| `ADMIN_PASSWORD` | Strong bootstrap password of at least 12 characters on first start |
| `PAYMENT_WEBHOOK_SECRET` | Optional independent secret of at least 32 characters; required only for adapter webhooks |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_BOT_USERNAME` | Optional BotFather credentials; enable the `telegram` Compose profile to run delivery. See [Telegram](TELEGRAM.md). |

Generate secrets locally with `python -c "import secrets; print(secrets.token_urlsafe(48))"`. Store them in the deployment environment; never commit `.env`. Remove the bootstrap password from configuration after successful initialization, and change the password through the app.

Put a TLS reverse proxy on the same host in front of `127.0.0.1:8000`. The default Docker command does not trust forwarded headers. If you require individual client IP rate limits through a proxy, configure Uvicorn to trust only that proxy's exact source IP; do not enable unbounded trust of forwarded headers. Without this, clients behind a proxy share a rate-limit bucket.

Use one Uvicorn worker. Store the database on local durable disk, not a network filesystem. The rootless Docker image runs as UID 10001; ensure bind-mounted data directories are writable by that user. Do not set production mode until HTTPS, device integration and failure recovery have been tested.

## Backup

The `data/` directory contains the SQLite database, its WAL files and (in development when no APP_SECRET is set) `.app-key`. Preserve the application secret separately and securely: losing it invalidates stored sessions and collection credentials.

For a running native instance:

```bash
python scripts/backup.py --source data/parcelhub.sqlite3 backups/parcelhub-2026-10-15.sqlite3
```

The script uses SQLite's backup API, verifies integrity, creates a new mode-0600 file and never overwrites an existing backup. Do not copy only the main `.sqlite3` file while the application is writing: recent changes may be in the WAL.

For Docker, run a backup tool/container with access to the named volume, or stop the web service **and Telegram worker** before backing up the entire volume. To restore, stop both processes, restore the verified database to a fresh data directory, restore the same APP_SECRET, ensure correct ownership, and restart. Retain the old volume until the restored installation is verified. Restored staging copies must not run with live Telegram credentials because their outbox can contain pending messages.

## Operations checklist

1. Register recipient accounts and confirm campus identity locally before accepting real parcels. This release does not verify email ownership or integrate with SSO.
2. Confirm the physical bay mapping, relay pulse limits, sensor polarity and fail-safe behaviour with the installer.
3. Exercise normal deposit, empty-deposit cancellation, incorrect OTP, expired OTP, payment waiting, door jam, network loss and power recovery.
4. Verify that an unauthenticated device cannot actuate a locker and a recipient cannot see another recipient's records.
5. Train authorized staff to use manual recovery only after physical inspection. Recording collection manually is an exception and is logged.
6. Establish a physical access policy, maximum retention period, return/refund process, account recovery process and a data retention policy before real use.
7. Monitor `/api/health` and process logs. Health indicates app/database availability, not proof that every physical locker is working.

## Known limits

- No live DuitNow checkout, WhatsApp, SMS or verified campus identity is configured.
- Telegram delivery is optional and requires a configured bot plus its worker. Tests use a fake transport; live delivery must be checked after configuration.
- No automatic provider refund, account deletion, password reset email or expired parcel return process.
- Six-digit codes have a fixed per-client-IP request limit; a large kiosk fleet needs per-device identity and distributed rate limiting.
- Camera scanning uses the browser's `BarcodeDetector`. Where unavailable, OTP and pasted QR payload remain available; camera access requires HTTPS or localhost.
- One physical station only. No multi-tenant permission boundaries.
- Application tests passed locally. A browser screenshot review and Docker daemon build could not be performed in the authoring environment. The GitHub workflow includes a Docker build; physical operation needs an on-site pilot.
