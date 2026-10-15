# Integration contracts

## Physical locker controller

The supplied frontend's door animation is a representation, not proof that a relay operated. In `HARDWARE_MODE=device`, browser endpoints cannot confirm sensor events. Use a dedicated PAP-01 controller and set the same `DEVICE_TOKEN` on the application and controller.

Every request must have `Authorization: Bearer <DEVICE_TOKEN>`. Use HTTPS outside loopback testing. Never expose the token in frontend JavaScript or a public repository.

1. Poll `GET /api/device/commands` every 2–5 seconds.
2. For each new `queued` command, look up the fixed `locker_id` in a controller-side allowlist. Store command IDs durably and never pulse the same command twice after a retry/reboot.
3. Actuate the mapped lock using a bounded pulse. Report `opened` only after the door sensor confirms it.
4. After closure, report `closed` and explicit `parcel_present`. A door sensor cannot determine parcel presence on its own; use an independent sensor or trusted local confirmation.
5. If there is a fault, report `fault` with a concise description. Do not automatically retry the lock. Staff must inspect it.

Example queued response:

```json
{
  "station_id": "PAP-01",
  "commands": [
    {"id":"CMD-...","parcel_id":"PH-...","locker_id":"A02","kind":"PICKUP","state":"queued","created_at":1792000000}
  ]
}
```

Report events to `POST /api/device/commands/{command_id}/events`:

```json
{"event":"opened"}
```

```json
{"event":"closed","parcel_present":false}
```

```json
{"event":"fault","detail":"Door sensor did not change after relay pulse"}
```

Closed events are idempotent after completion; repeated open acknowledgement is accepted while open. A close-before-open event is rejected. A command with no open acknowledgement after 90 seconds is marked faulty by the next one-minute housekeeping run. This is an application timeout, not the relay's electrical pulse duration.

A user must never be allowed to supply GPIO numbers to the controller. Validate bay ID, command type and phase locally. Physical emergency access, electrical protection, watchdog behaviour and power-loss recovery are installer responsibilities and need separate hardware tests.

### Exercise the contract locally

Start an isolated app with `HARDWARE_MODE=device` and a long random `DEVICE_TOKEN` (keep `APP_ENV=development` for local HTTP). Then run:

```bash
python scripts/device_simulator.py --base-url http://127.0.0.1:8000
```

The script is an **interactive staging simulator**, not ESP32 firmware. It uses the real polling/acknowledgement API and asks before reporting each sensor event. It drives no hardware.

## Payment provider adapter

Demo buttons are disabled when `DEMO_MODE=false`. The included operational UI uses counter payments: the recipient obtains a reference and the operator confirms actual receipt. For an automated gateway, implement an adapter that:

1. Creates a checkout with a supported provider, tied to the server-issued `PAY-...` reference and exact sen amount.
2. Verifies the provider's own authenticated settlement callback independently.
3. Translates only confirmed successful MYR settlements into the signed event below.
4. Reconciles late/expired/cancelled intents and refunds with an operator. The app intentionally rejects these for automatic credit.

There is no built-in live DuitNow checkout or provider credentials. Do not sign callbacks directly from the browser. Configure the adapter and server with the same separate `PAYMENT_WEBHOOK_SECRET` (32+ characters).

POST `/api/payments/webhook`, `Content-Type: application/json`:

```json
{
  "event_id": "provider-unique-event-id",
  "payment_id": "PAY-...",
  "amount_cents": 150,
  "currency": "MYR",
  "status": "succeeded"
}
```

Headers:

- `X-Payment-Timestamp`: current UTC epoch seconds.
- `X-Payment-Signature`: lowercase hexadecimal HMAC-SHA256 of `timestamp + "." + raw_request_body`, keyed by `PAYMENT_WEBHOOK_SECRET`.

The signature authenticates the original body bytes, including whitespace. Timestamps outside ±300 seconds, mismatched amount/currency and expired intents are rejected. Duplicate event IDs are acknowledged without adding money twice. Neither a frontend click nor intent creation is proof of payment.

Local staging example:

```bash
python scripts/payment_event.py PAY-REFERENCE 50 --event-id staging-001 --confirm-staging
```

This helper changes the target application's payment state and makes **no provider payment**. Use only an isolated staging installation.

## Notifications

In-app notifications are scoped to each recipient. Optional Telegram delivery uses a dedicated Bot API worker, private-chat account linking and a transactional outbox. See [Telegram setup and operations](TELEGRAM.md).

Automatic overdue reminders are created every 12 hours while the web app is running. The same transaction queues Telegram delivery only for an already linked account. Creating an inbox item or queue entry is not proof of delivery; `sent` means Telegram accepted the message, not that the user read it.

Email, WhatsApp and SMS delivery are not implemented. Email remains an account/login identifier.
