"""In-process HTTP adapter for DOM integration tests; never opens a network port."""

import json
import sys
from tempfile import TemporaryDirectory
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app

with TemporaryDirectory() as folder:
    with TestClient(
        create_app(Settings(folder + "/test.sqlite3", "ui-test-secret-" * 4))
    ) as client:
        for line in sys.stdin:
            item = json.loads(line)
            response = client.request(
                item["method"],
                item["url"],
                headers=item.get("headers"),
                content=item.get("body"),
            )
            try:
                body = response.json()
            except ValueError:
                body = {"detail": response.text}
            print(
                json.dumps(
                    {"id": item["id"], "status": response.status_code, "body": body}
                ),
                flush=True,
            )
