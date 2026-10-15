import hashlib
import hmac
import secrets


def password_hash(password):
    salt = secrets.token_hex(16)
    digest = hashlib.scrypt(
        password.encode(), salt=salt.encode(), n=16384, r=8, p=1
    ).hex()
    return f"scrypt${salt}${digest}"


def password_matches(password, encoded):
    try:
        _, salt, expected = encoded.split("$")
        actual = hashlib.scrypt(
            password.encode(), salt=salt.encode(), n=16384, r=8, p=1
        ).hex()
        return hmac.compare_digest(expected, actual)
    except (ValueError, TypeError):
        return False


def fingerprint(value, secret):
    return hmac.new(secret.encode(), value.encode(), hashlib.sha256).hexdigest()


def token():
    return secrets.token_urlsafe(32)
