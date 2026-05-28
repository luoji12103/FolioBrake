"""CSRF protection utilities for state-changing API endpoints.

Provides token generation and validation using timing-safe comparison.
Use for form-based or cookie-based authentication flows.
"""
from __future__ import annotations

import secrets


def generate_csrf_token() -> str:
    return secrets.token_hex(32)


def validate_csrf_token(token: str, stored: str) -> bool:
    if not token or not stored:
        return False
    return secrets.compare_digest(token, stored)
