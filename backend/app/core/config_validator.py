from app.core.config import settings

def validate_config():
    errors = []
    if not settings.DATABASE_URL:
        errors.append("DATABASE_URL is required")
    if not settings.REDIS_URL:
        errors.append("REDIS_URL is required")
    return errors
