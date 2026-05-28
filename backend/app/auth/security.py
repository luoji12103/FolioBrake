"""Authentication and security utilities.

Supports both the new PyJWT/bcrypt path and legacy HMAC/PBKDF2 hashes
so existing users can log in without a forced password reset.
"""
from __future__ import annotations

import re
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.core.config import settings

SECRET_KEY: str = settings.SECRET_KEY
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_SECONDS: int = 3600
REFRESH_TOKEN_EXPIRE_SECONDS: int = 604800

TOKEN_EXPIRY_SECONDS = ACCESS_TOKEN_EXPIRE_SECONDS

_MIN_PASSWORD_LENGTH = 8
_PASSWORD_SPECIAL_RE = re.compile(r'[!@#$%^&*(),.?":{}|<>]')


def validate_password_strength(password: str) -> str | None:
    if len(password) < _MIN_PASSWORD_LENGTH:
        return f"Password must be at least {_MIN_PASSWORD_LENGTH} characters"
    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter"
    if not re.search(r"\d", password):
        return "Password must contain at least one digit"
    if not _PASSWORD_SPECIAL_RE.search(password):
        return "Password must contain at least one special character"
    return None


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify plaintext against a bcrypt or legacy PBKDF2 hash."""
    if "$" in hashed and not hashed.startswith("$2"):
        try:
            import hmac as _hmac
            salt, pw_hash_hex = hashed.split("$", 1)
            computed = hashlib.pbkdf2_hmac(
                "sha256", password.encode(), salt.encode(), 100_000
            )
            return _hmac.compare_digest(computed.hex(), pw_hash_hex)
        except (ValueError, AttributeError):
            return False

    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_token(user_id: int, username: str) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "username": username,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(seconds=ACCESS_TOKEN_EXPIRE_SECONDS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: int, username: str) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "username": username,
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(seconds=REFRESH_TOKEN_EXPIRE_SECONDS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict[str, Any] | None:
    """Decode and verify a JWT, falling back to legacy HMAC tokens."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        pass

    try:
        import base64, hmac as _hmac, json as _json, time as _time
        token_body, signature = token.rsplit(".", 1)
        payload_bytes = base64.urlsafe_b64decode(token_body)
        expected_sig = _hmac.new(
            SECRET_KEY.encode(), payload_bytes, hashlib.sha256
        ).hexdigest()
        if not _hmac.compare_digest(signature, expected_sig):
            return None
        payload = _json.loads(payload_bytes)
        if payload.get("exp", 0) < _time.time():
            return None
        return payload
    except Exception:
        return None


def refresh_access_token(refresh_token: str) -> str | None:
    payload = verify_token(refresh_token)
    if payload is None or payload.get("type") != "refresh":
        return None
    user_id = payload.get("sub")
    username = payload.get("username", "")
    if user_id is None:
        return None
    return create_token(int(user_id), username)


def generate_api_key() -> tuple[str, str]:
    raw_key = secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    return raw_key, key_hash


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()
