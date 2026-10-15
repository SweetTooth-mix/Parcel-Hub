from dataclasses import dataclass, field
from pathlib import Path
import os
import secrets
import re


@dataclass(frozen=True)
class Settings:
    database: str
    secret: str
    demo: bool = True
    secure_cookies: bool = False
    hardware_mode: str = "simulated"
    device_token: str = ""
    payment_secret: str = ""
    admin_email: str = ""
    admin_password: str = ""
    origin: str = ""
    session_hours: int = 12
    telegram_bot_token: str = field(default="", repr=False)
    telegram_bot_username: str = ""

    @property
    def telegram_enabled(self):
        return bool(self.telegram_bot_token and self.telegram_bot_username)

    @classmethod
    def from_env(cls):
        os.umask(0o077)
        production = os.getenv("APP_ENV", "development") == "production"
        demo = (
            os.getenv("DEMO_MODE", "false" if production else "true").lower() == "true"
        )
        folder = Path(os.getenv("DATA_DIR", "./data"))
        folder.mkdir(parents=True, exist_ok=True)
        key = os.getenv("APP_SECRET", "")
        if production and (len(key) < 32 or demo):
            raise RuntimeError(
                "Production requires APP_SECRET (32+ characters) and DEMO_MODE=false."
            )
        if not key:
            keyfile = folder / ".app-key"
            if not keyfile.exists():
                fd = os.open(keyfile, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(fd, "w") as f:
                    f.write(secrets.token_hex(32))
            key = keyfile.read_text().strip()
        mode = os.getenv("HARDWARE_MODE", "simulated")
        if mode not in ("simulated", "device"):
            raise RuntimeError("HARDWARE_MODE must be simulated or device.")
        if mode == "device" and len(os.getenv("DEVICE_TOKEN", "")) < 32:
            raise RuntimeError(
                "Device mode requires a DEVICE_TOKEN of at least 32 characters."
            )
        if production and (
            mode != "device" or not os.getenv("APP_ORIGIN", "").startswith("https://")
        ):
            raise RuntimeError(
                "Production requires HARDWARE_MODE=device and an HTTPS APP_ORIGIN."
            )
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        bot_username = os.getenv("TELEGRAM_BOT_USERNAME", "").strip().lstrip("@")
        if bot_token and not re.fullmatch(r"[0-9]+:[A-Za-z0-9_-]+", bot_token):
            raise RuntimeError("TELEGRAM_BOT_TOKEN has an invalid format.")
        if bool(bot_token) != bool(bot_username) or (
            bot_username and not re.fullmatch(r"[A-Za-z0-9_]{5,32}", bot_username)
        ):
            raise RuntimeError(
                "Set both TELEGRAM_BOT_TOKEN and a valid TELEGRAM_BOT_USERNAME."
            )
        return cls(
            str(folder / "parcelhub.sqlite3"),
            key,
            demo,
            production,
            mode,
            os.getenv("DEVICE_TOKEN", ""),
            os.getenv("PAYMENT_WEBHOOK_SECRET", ""),
            os.getenv("ADMIN_EMAIL", ""),
            os.getenv("ADMIN_PASSWORD", ""),
            os.getenv("APP_ORIGIN", "").rstrip("/"),
            telegram_bot_token=bot_token,
            telegram_bot_username=bot_username,
        )
