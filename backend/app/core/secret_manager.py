from __future__ import annotations

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

_DEFAULT_MAX_AGE_DAYS = 90


def check_secret_age(
    secret_name: str,
    created_date: datetime,
    max_age_days: int = _DEFAULT_MAX_AGE_DAYS,
) -> bool:
    age = datetime.now() - created_date
    if age > timedelta(days=max_age_days):
        logger.warning(
            "Secret '%s' is %d days old (max %d). Consider rotation.",
            secret_name,
            age.days,
            max_age_days,
        )
        return False
    return True


def warn_on_weak_secret_key(secret_key: str) -> None:
    _WEAK_VALUES = {
        "",
        "replace-me",
        "change-me",
        "dev-secret-key",
        "dev-secret-key-change-in-production",
        "secret",
        "password",
    }
    if secret_key in _WEAK_VALUES or len(secret_key) < 16:
        logger.warning(
            "SECRET_KEY appears to be a weak placeholder. "
            "Generate a strong key with: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
        )
