"""Send one signed settlement event to a local/staging adapter endpoint."""

import argparse
import hashlib
import hmac
import json
import os
import time
import urllib.request
from urllib.parse import urlparse

p = argparse.ArgumentParser(
    description="Staging only: exercise a signed payment webhook. No provider payment is made."
)
p.add_argument("payment_id")
p.add_argument("amount_cents", type=int)
p.add_argument("--event-id", required=True)
p.add_argument("--base-url", default="http://127.0.0.1:8000")
p.add_argument(
    "--confirm-staging",
    action="store_true",
    help="Required: this marks an intent as paid in the target application.",
)
a = p.parse_args()
if not a.confirm_staging:
    p.error("Pass --confirm-staging only for an isolated staging application.")
url = a.base_url.rstrip("/")
parts = urlparse(url)
if parts.scheme != "https" and not (
    parts.scheme == "http" and parts.hostname in ("localhost", "127.0.0.1")
):
    p.error("Use HTTPS or loopback HTTP.")
secret = os.getenv("PAYMENT_WEBHOOK_SECRET", "")
if len(secret) < 32:
    p.error("Set PAYMENT_WEBHOOK_SECRET to the staging server secret.")
body = json.dumps(
    {
        "event_id": a.event_id,
        "payment_id": a.payment_id,
        "amount_cents": a.amount_cents,
        "currency": "MYR",
        "status": "succeeded",
    },
    separators=(",", ":"),
).encode()
ts = str(int(time.time()))
sig = hmac.new(secret.encode(), ts.encode() + b"." + body, hashlib.sha256).hexdigest()
req = urllib.request.Request(
    url + "/api/payments/webhook",
    data=body,
    headers={
        "Content-Type": "application/json",
        "X-Payment-Timestamp": ts,
        "X-Payment-Signature": sig,
    },
)
with urllib.request.urlopen(req, timeout=10) as response:
    print(response.read().decode())
