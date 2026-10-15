"""Interactive staging controller. Does not drive relays. Uses the real device contract."""

import argparse
import json
import os
import urllib.request
import urllib.error
from urllib.parse import urlparse

parser = argparse.ArgumentParser(
    description="Exercise the PAP-01 device API with explicit sensor events."
)
parser.add_argument("--base-url", default="http://127.0.0.1:8000")
args = parser.parse_args()
base = args.base_url.rstrip("/")
parsed = urlparse(base)
if parsed.scheme != "https" and not (
    parsed.scheme == "http" and parsed.hostname in ("127.0.0.1", "localhost")
):
    parser.error("Use HTTPS or loopback HTTP for local staging.")
secret = os.getenv("DEVICE_TOKEN", "")
if len(secret) < 32:
    parser.error(
        "Set DEVICE_TOKEN to the same staging device token used by the server."
    )


def request(path, payload=None):
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(
        base + path,
        data=data,
        headers={
            "Authorization": "Bearer " + secret,
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=8) as response:
        return json.load(response)


print("STAGING SIMULATOR: no physical relay or sensor is connected. Ctrl-C to exit.")
while True:
    try:
        commands = request("/api/device/commands")["commands"]
        if not commands:
            input("No pending commands. Press Enter to poll again. ")
            continue
        for command in commands:
            print(
                f"{command['id']} | {command['locker_id']} | {command['kind']} | {command['state']}"
            )
            if command["state"] == "queued":
                choice = (
                    input("Confirm simulated door OPEN? [y/N/fault]: ").strip().lower()
                )
                if choice == "fault":
                    detail = (
                        input("Fault description: ").strip() or "Staging fault test"
                    )
                    request(
                        "/api/device/commands/" + command["id"] + "/events",
                        {"event": "fault", "detail": detail},
                    )
                    continue
                if choice != "y":
                    continue
                request(
                    "/api/device/commands/" + command["id"] + "/events",
                    {"event": "opened"},
                )
            choice = input("Confirm door CLOSED? [y/N]: ").strip().lower()
            if choice == "y":
                present = input("Parcel still INSIDE? [y/N]: ").strip().lower() == "y"
                request(
                    "/api/device/commands/" + command["id"] + "/events",
                    {"event": "closed", "parcel_present": present},
                )
    except KeyboardInterrupt:
        print("\nStopped.")
        break
    except urllib.error.HTTPError as exc:
        print(f"API rejected request: HTTP {exc.code}; {exc.read().decode()[:300]}")
    except (OSError, ValueError) as exc:
        print("Request failed:", exc)
        input("Press Enter to retry. ")
