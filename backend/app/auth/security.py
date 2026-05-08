"""Authentication and security utilities.

Uses stdlib hashlib + secrets for password hashing and token generation.
No external JWT dependency required — uses HMAC-signed tokens.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
import base64
from typing import Any

from app.core.config import settings

SECRET_KEY = settings.SECRET_KEY
TOKEN_EXPIRY_SECONDS = 86400  # 24 hours


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    pw_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return f"{salt}${pw_hash.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    try:
        salt, pw_hash_hex = hashed.split("$", 1)
    except ValueError:
        return False
    computed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return hmac.compare_digest(computed.hex(), pw_hash_hex)


def create_token(user_id: int, username: str) -> str:
    payload = {
        "sub": user_id,
        "username": username,
        "exp": int(time.time()) + TOKEN_EXPIRY_SECONDS,
    }
    payload_bytes = json.dumps(payload, sort_keys=True).encode()
    signature = hmac.new(SECRET_KEY.encode(), payload_bytes, hashlib.sha256).hexdigest()
    token_body = base64.urlsafe_b64encode(payload_bytes).decode()
    return f"{token_body}.{signature}"


def verify_token(token: str) -> dict[str, Any] | None:
    try:
        token_body, signature = token.rsplit(".", 1)
    except ValueError:
        return None

    payload_bytes = base64.urlsafe_b64decode(token_body)
    expected_sig = hmac.new(SECRET_KEY.encode(), payload_bytes, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(signature, expected_sig):
        return None

    payload = json.loads(payload_bytes)
    if payload.get("exp", 0) < time.time():
        return None

    return payload


def generate_api_key() -> tuple[str, str]:
    raw_key = secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    return raw_key, key_hash


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()
