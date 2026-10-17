# Telegram orders and notifications

## Setup

Create a dedicated bot using `/newbot` in [@BotFather](https://t.me/BotFather). Set its token and username in the server environment, or in `.env` for Docker Compose:

```dotenv
TELEGRAM_BOT_TOKEN=
TELEGRAM_BOT_USERNAME=
```

Keep the token out of source control, browser code, screenshots and chat. If exposed, revoke it in BotFather and update the server. A new token for the same bot keeps existing account links. The worker checks the bot's identity and refuses to use a different bot with an already linked database.

Run `docker compose --profile telegram up --build -d`. The optional `telegram` service shares the application's persistent database and starts after the web service is healthy. Without the profile, the web application and in-app inbox still work. Native Python users run `python -m app.telegram` in a second terminal with the **same environment and DATA_DIR** as the web process. `.env` is not automatically loaded by Python.

The worker uses outbound HTTPS long polling, not an inbound webhook. No public domain is needed for a local demo. Use one worker and one dedicated bot. A bot with an existing webhook is rejected; the worker never deletes another application's webhook. HTTPS `APP_ORIGIN` is optional and adds a portal link to parcel messages. It must be the application's actual origin.

## Connect an account

1. Register/log in to your own ParcelHub account. Shared demo accounts should not be linked to personal Telegram chats.
2. In **Akaun & sistem**, choose **Sambung Telegram**.
3. Open the private link and press **Start** in Telegram. Opening the link alone is insufficient.
4. Return to the portal and choose **Saya sudah tekan Start**. Check the displayed Telegram account.
5. Choose **Hantar mesej ujian**. The UI initially reports queued, not delivered. Refresh its status after receiving the message.

Link tokens are random, stored only as keyed hashes, single-use and valid for ten minutes. Creating another link revokes the previous link. Linking is accepted only in a private chat whose sender matches the chat ID. Each Telegram chat can link to only one ParcelHub account; changing it requires disconnecting first. Password changes revoke unused linking tokens.

New order and parcel notifications are forwarded after linking; old inbox items are not replayed. After confirmed storage, the recipient receives the six-digit pickup OTP, locker and expiry in their linked private chat. QR tokens and passwords are not sent. The current OTP is also visible on the web; reading it does not rotate it. Explicit regeneration invalidates the previous OTP, QR and pickup sessions. The bot supports role-specific menus, `/help` and `/stop`. Disconnecting in the portal or sending `/stop` removes the subscription and cancels queued messages. Blocking the bot also disconnects the subscription when the worker receives the block event or a forbidden response. An already in-flight message can still arrive.

Telegram sends real messages even when parcel/payment data is in demo mode. It is disabled by default. No email notification delivery is configured.

## Customer and worker menus

Customers first register on the web and connect their own account; the bot cannot create or select an identity from a typed name or email.

- **Order baharu** or `/order`: tracking → courier → estimated size → optional notes → **Hantar order**. Nothing is submitted before confirmation. Drafts persist across worker restarts for 30 minutes.
- **Order saya** or `/orders`: up to six recent/prioritized orders, current status and available pickup codes. The full portal list is available on the web.
- `/code ORD-ID`: retrieve the same current code for a ready parcel; issue a new one if expired. Before storage or after collection it is refused.
- `/cancel`: discard the draft. `/cancel_order ORD-ID`: cancel an order only before a worker accepts it.

Workers connect their own operator/admin account in the same way. Every operator/admin receives new-order notifications in the web inbox; linked workers also receive Telegram notifications.

- **Tugasan** or `/tasks`: incoming and assigned work, with action buttons.
- `/accept ORD-ID`: claim the order. Only one worker can claim it.
- `/store ORD-ID`: allocate an available locker for the estimated size. `/store ORD-ID L` overrides the actual size (S/M/L/XL). This starts a door command; it does not mark the parcel ready.
- `/stored ORD-ID`: simulated storage confirmation only. In device mode, the controller must acknowledge the door opening and closing with parcel presence. The bot cannot bypass this.
- `/reject ORD-ID reason`: decline a pending/own accepted order, notifying the customer with the reason.

A worker who cannot find a suitable bay can choose another size/bay in the web portal or retry later. An accepted order remains queued for that worker. All commands apply the same permissions, validations and transactions as the web API. See [order states](ORDERS.md).

## Delivery behaviour

- Inbox and outbox records commit in the same database transaction. Network calls happen in the worker, outside the transaction.
- OTPs are not stored as plaintext in the inbox/outbox. A random nonce and the server APP_SECRET derive the current OTP/QR using domain-separated HMAC; verification still uses keyed hashes. The worker resolves the current code immediately before delivery. Queued code notifications are cancelled if their code has expired, been replaced or been used. Already sent or in-flight messages cannot be recalled; the server always rejects invalid codes.
- Command updates and their offset commit together, preventing a repeated update from repeating an order. Interactive replies are best effort; if one is lost, use `/orders`, `/tasks` or restart `/order`. Durable event notifications retry through the outbox.
- The outbox is persistent across restarts. A message is marked sent only after a successful Bot API response. This confirms Telegram acceptance, not a read receipt.
- Temporary failures use exponential retry delays, capped at ten minutes, with up to eight attempts. Telegram flood limits honour `retry_after`. Undelivered messages expire after 24 hours to avoid replaying a long stale backlog.
- Invalid-message errors fail that message; blocked-chat errors disconnect the subscription. Authentication errors stop the worker until the token is corrected. Failed messages remain visible as a count in the user's settings; their in-app copies remain available.
- **Duplicate messages are possible**: if Telegram accepts a message but the connection fails before the worker stores the result, a retry may duplicate it. `sendMessage` provides no application idempotency key. The database prevents normal duplicate queue entries for one notification and uses a short lease to recover interrupted sends.
- Pending messages retain their original connection ID, so disconnecting and linking another chat never redirects the old queue to that chat.

## Troubleshooting

```bash
docker compose --profile telegram logs --tail 100 telegram
```

| Symptom | Check |
| --- | --- |
| Telegram belum diaktifkan | Both Telegram environment variables must be set; recreate the web and worker containers after changes. |
| Bot belum tersedia | Check the worker is running, the server can reach Telegram, the token/username match, and this bot has no webhook. A stopped worker is detected after about 90 seconds. |
| Pautan tidak sah / tamat tempoh | Generate a new link and press Start within ten minutes. Never share this link. |
| Account already linked | Disconnect the previous account/chat first. No user can silently replace another user's subscription. |
| API error 401 | Token is invalid or revoked. Update it and restart the services. |
| API error 409 | Another poller or webhook is using the bot. Stop the duplicate worker or use a dedicated bot. |
| Messages pending | Check worker connectivity; a Telegram rate limit or temporary failure is retried automatically. |
| Messages failed | Correct the underlying issue, then send a fresh test message. The in-app inbox remains the source of truth. |

API errors are logged as numeric codes only. The worker does not log tokens, request URLs, linking tokens or message bodies. Backups include Telegram chat IDs and the delivery queue and should receive the same protection as other user data. Do not run a restored test database with the live bot credentials: doing so can replay pending deliveries.

## API and validation

Authenticated, account-scoped endpoints: `GET /api/telegram`, `POST /api/telegram/link`, `POST /api/telegram/disconnect`, `POST /api/telegram/test`. Writes require the existing CSRF token. Test messages are limited to one per minute per account. Chat IDs and bot credentials are not returned by these endpoints. There is no browser-accessible endpoint for injecting Telegram updates.

Automated tests use a fake Telegram transport and never send external messages. A live acceptance check requires a configured bot and a user's explicit opt-in through Start.

References: [deep linking](https://core.telegram.org/bots/features#deep-linking), [getUpdates](https://core.telegram.org/bots/api#getupdates), [sendMessage](https://core.telegram.org/bots/api#sendmessage), [response parameters](https://core.telegram.org/bots/api#responseparameters).
