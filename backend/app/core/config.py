from __future__ import annotations

import os
import secrets
import logging

from pydantic_settings import BaseSettings
from pydantic import field_validator

logger = logging.getLogger(__name__)


def _default_secret_key() -> str:
    return secrets.token_urlsafe(32)


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    APP_ENV: str = "dev"
    DATABASE_URL: str = "postgresql+psycopg://guardian:guardian@localhost:5432/guardian"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = _default_secret_key()
    DATA_DIR: str = "./data"
    TUSHARE_TOKEN: str = ""
    ENABLE_INTRADAY_MONITORING: bool = False
    DEFAULT_RISK_PROFILE: str = "balanced"

    API_KEYS: str = ""
    CORS_ORIGINS: str = ""
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = True
    RATE_LIMIT_CALLS: int = 100
    RATE_LIMIT_PERIOD: int = 60

    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    REDIS_MAX_CONNECTIONS: int = 20

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v:
            raise ValueError("DATABASE_URL is required")
        if "guardian:guardian" in v and os.environ.get("APP_ENV", "dev") == "production":
            raise ValueError("Default database credentials must not be used in production")
        return v


settings = Settings()
