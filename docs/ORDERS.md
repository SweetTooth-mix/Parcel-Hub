# Customer-first parcel orders

Customers request storage through **Order baharu** on the web or `/order` in the linked Telegram bot. Each order belongs to the signed-in/linked customer; payloads cannot choose another recipient. Registration and Telegram linking happen on the web first. Workers use **Tugasan** or `/tasks`.

## States

| Order shown in web/bot | Meaning | Next action |
| --- | --- | --- |
| Menunggu pekerja | Pending request; no locker reserved, no fee clock or pickup code | Worker accepts, customer cancels, or worker rejects with reason |
| Diterima pekerja | Assigned to one worker | Assigned worker receives the parcel physically and starts storage |
| Sedang disimpan | Locker reserved; door command started | Confirm door closed with parcel present |
| Sedia diambil | Storage confirmed; fee clock starts, OTP/QR issued | Customer uses code at kiosk, reviews fees and pays |
| Menunggu pintu / Pintu terbuka | Pickup underway | Controller/simulator confirms parcel removed and door closed |
| Selesai diambil | Collection complete | History and receipt remain; pickup code is invalid |
| Perlu bantuan | Door/device problem | Admin inspects and uses existing recovery controls |
| Dibatalkan / Ditolak | Request ended | Reason remains visible to customer |

The order stores its request/assignment state and links to one parcel. Once fulfilling, its displayed status follows that parcel's authoritative device/payment state, avoiding a separate diverging fulfillment status. An empty initial deposit returns the order to accepted; retry reuses its parcel record. Only the assigned worker can start/confirm storage, including the legacy deposit-confirmation endpoint.

## Notifications and codes

Every newly created order writes a customer acknowledgement and staff inbox notifications. Linked accounts get the same event through the durable Telegram outbox. Accepting a task tells the customer it is being processed. Storing/issuing a door command alone does not produce an OTP.

Confirmed storage generates a six-digit OTP plus a QR credential, both valid for 72 hours. The customer sees the OTP on their order card, in the web inbox and in their linked private chat; QR is available in the web code dialog. Viewing a valid code does not replace it. **Jana semula kod** explicitly replaces both credentials and revokes existing pickup sessions. Expired/legacy codes can be renewed on demand. Staff see operational parcel details without the customer code.

Code validation, payment and physical pickup continue through the existing kiosk/device workflow. In device mode, web and bot confirmations cannot simulate a sensor event. In demo mode, the worker must explicitly confirm after placing the parcel and closing the door.

## API

All endpoints require an authenticated account; writes require CSRF. All mutations use the existing SQLite immediate transaction.

| Endpoint | Who | Result |
| --- | --- | --- |
| `GET /api/orders` | Any account | Up to 200 orders, prioritizing pending/accepted/device issues; recipient sees own orders only |
| `POST /api/orders` | Recipient | Create with tracking, courier, estimated size and optional notes |
| `GET /api/orders/{id}` | Owner/staff | Order, related parcel and owner-only current code |
| `POST /api/orders/{id}/cancel` | Owner | Cancel before acceptance |
| `POST /api/orders/{id}/accept` | Staff | Claim one pending request |
| `POST /api/orders/{id}/reject` | Staff | Reject pending/own accepted request with reason |
| `POST /api/orders/{id}/store` | Assigned staff | Reserve a locker/start deposit; optional actual size and locker ID |
| `POST /api/orders/{id}/confirm` | Assigned staff | Simulated confirmation only |
| `GET /api/parcels/{id}/code` | Owner | Retrieve current valid code without rotating it; 409 if unavailable |
| `POST /api/parcels/{id}/code` | Owner | Explicitly issue new OTP/QR for a ready parcel |

Tracking is normalized, bounded and unique among active requests/existing parcels. Retrying an identical customer request returns its existing order without repeating notifications. Different details or another customer with the same tracking receive a conflict. A customer may have up to 20 pending/accepted requests. All claims and locker reservations are atomic. Store/confirm retries are idempotent while the parcel remains reserved/ready. Existing manual deposit remains available as **Simpanan manual**, but cannot bypass a pending order with the same tracking.

## Migration and rollout

Schema version 3 adds `orders`, `telegram_drafts`, `pickup_credentials` and `notification_codes` without rebuilding existing tables. Back up the database and retain APP_SECRET before upgrading. Existing parcels and linked accounts remain usable; a legacy ready parcel gets a recoverable current code on its next explicit code request. The code nonce is stored separately from the server secret; no plaintext OTP/QR is saved in notification or outbox text.

Restart both web and Telegram worker using the same code/database/secret. No extra dependency or environment variable is required beyond the existing Telegram setup. Confirm receipt using a dedicated linked account; unit tests use fake Telegram transport and send no real messages. Emails remain disabled. Phone layout needs a rendered-browser/device check before a production pilot; automated DOM coverage is functional rather than visual.
