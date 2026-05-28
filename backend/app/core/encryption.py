"""Field-level encryption for sensitive data at rest.

Uses Fernet symmetric encryption (AES-128-CBC with HMAC-SHA256).
The encryption key is derived from ``settings.SECRET_KEY`` via PBKDF2
so no extra secret management is needed.

Usage::

    from app.core.encryption import encrypt_field, decrypt_field

    encrypted = encrypt_field("sensitive-value")
    original = decrypt_field(encrypted)
"""
from __future__ import annotations

import base64
import hashlib
import os
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings

_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        key_material = hashlib.pbkdf2_hmac(
            "sha256",
            settings.SECRET_KEY.encode("utf-8"),
            b"folio-brake-encryption-salt",
            480_000,
        )
        fernet_key = base64.urlsafe_b64encode(key_material)
        _fernet = Fernet(fernet_key)
    return _fernet


def encrypt_field(plaintext: str) -> str:
    """Encrypt a string value. Returns a Fernet token as a UTF-8 string."""
    return _get_fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_field(ciphertext: str) -> str | None:
    """Decrypt a Fernet-encrypted string. Returns ``None`` on failure."""
    try:
        return _get_fernet().decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except (InvalidToken, Exception):
        return None
