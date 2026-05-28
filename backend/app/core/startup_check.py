import logging
from app.db.base import SessionLocal
from sqlalchemy import text

logger = logging.getLogger(__name__)

def check_database():
    try:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            return True
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Database startup check failed: {e}")
        return False

def check_redis():
    try:
        import redis
        r = redis.Redis(host="redis", port=6379, socket_connect_timeout=2)
        r.ping()
        return True
    except Exception as e:
        logger.warning(f"Redis startup check failed: {e}")
        return False
