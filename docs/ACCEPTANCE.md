# Acceptance scenarios

Use a fresh demo database and test desktop and phone layouts in a normal browser. Node DOM tests exercise interactions but do not render pixels.

| Scenario | Action | Expected result |
| --- | --- | --- |
| Standard collection | Recipient gets code; kiosk pays, opens, closes empty | Only that parcel is collected; bay becomes available; receipt and notification exist |
| Overdue parcel | Collect initial demo parcel B01 | Base RM1 plus RM1 for the first late six-hour block |
| Invalid code | Enter six incorrect digits | Generic rejection; no name or parcel disclosure |
| Reissued code | Generate a second code | Previous OTP, QR and pickup session become invalid |
| Abandoned pickup | Close door with parcel still inside | Parcel remains READY; payment is retained; it can be retried |
| Deposit | Operator reserves a bay, puts parcel in and closes | Not READY until storage confirmation; recipient receives an in-app notification |
| Empty deposit | Operator closes without parcel | Reservation cancelled and bay released |
| Concurrent deposit | Two submissions target same free bay | Exactly one succeeds |
| Access isolation | Recipient opens another parcel ID or admin URL | Denied by API, even if UI is bypassed |
| Maintenance | Admin disables an empty bay | New parcels cannot be assigned; enabling restores availability |
| Device delay | In device mode, do not acknowledge an unlock | No collection recorded; command marked faulty after timeout sweep |
| Manual recovery | Admin records physical inspection | Reason and actor audited; unsafe state transitions rejected |
| Duplicate payment | Replay identical signed provider event | Balance credited once |
| Restart | Restart app/container after a collection | State and receipts persist |
| Small screen | Open at 390px width | Menu collapses; kiosk form is before the model; tables scroll within their container |
| Keyboard access | Tab through login, code, modal and actions | Visible focus indicators, labelled inputs, modal can close with Escape |
| Reduced motion | Enable OS reduce motion | Cabinet and feedback animations stop |
| Telegram linking | Configure the bot/worker; use a personal account and press Start through its private link | Only that account is connected; reusing/expiring the link fails; groups are ignored |
| Telegram delivery | Link, send a test, then complete a parcel transaction | Queued changes to sent after Bot API acceptance; no OTP/QR is included |
| Telegram outage | Simulate a temporary transport error | Parcel/inbox changes commit; queued delivery retries without blocking the web app |
| Telegram opt-out | Disconnect or send /stop with a pending message | Pending message is cancelled; linking another chat does not redirect the old queue |

Telegram tests use a fake transport. Check actual chat delivery only after configuring a dedicated bot and explicitly connecting your own account. The default demo sends no external messages.

For a real device, verify relay operation and independent door/parcel sensing. A close sensor alone does not prove parcel removal; supply a parcel-presence sensor or a documented trusted operator confirmation.
