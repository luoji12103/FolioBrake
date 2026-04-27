import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_ENV: str = "dev"
    DATABASE_URL: str = "postgresql+psycopg://guardian:guardian@localhost:5432/guardian"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "replace-me"
    DATA_DIR: str = "./data"
    TUSHARE_TOKEN: str = ""
    ENABLE_INTRADAY_MONITORING: bool = False
    DEFAULT_RISK_PROFILE: str = "balanced"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
