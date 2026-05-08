import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    APP_ENV: str = "dev"
    DATABASE_URL: str = "postgresql+psycopg://guardian:guardian@localhost:5432/guardian"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "replace-me"
    DATA_DIR: str = "./data"
    TUSHARE_TOKEN: str = ""
    ENABLE_INTRADAY_MONITORING: bool = False
    DEFAULT_RISK_PROFILE: str = "balanced"

    API_KEYS: str = ""
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = True
    RATE_LIMIT_CALLS: int = 100
    RATE_LIMIT_PERIOD: int = 60

    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    REDIS_MAX_CONNECTIONS: int = 20


settings = Settings()
