"""API key authentication.

Valid API keys are stored in the ``API_KEYS`` setting (comma-separated).
The primary key is ``settings.SECRET_KEY`` as a fallback for dev convenience.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

_valid_keys: set[str] | None = None


def _load_keys() -> set[str]:
    global _valid_keys
    if _valid_keys is None:
        raw = getattr(settings, "API_KEYS", "")
        _valid_keys = {k.strip() for k in raw.split(",") if k.strip()}
        if not _valid_keys:
            _valid_keys = {settings.SECRET_KEY}
    return _valid_keys


async def verify_api_key(api_key: str | None = Security(_api_key_header)) -> str:
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
        )
    if api_key not in _load_keys():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
    return api_key
