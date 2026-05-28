import logging

logger = logging.getLogger(__name__)

class HealthChecker:
    def check_database(self) -> bool:
        try:
            from app.db.base import SessionLocal
            from sqlalchemy import text
            db = SessionLocal()
            try:
                db.execute(text("SELECT 1"))
                return True
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Database health check failed: {e}")
            return False
    
    def check_redis(self) -> bool:
        try:
            import redis
            r = redis.Redis(host="redis", port=6379, socket_connect_timeout=2)
            r.ping()
            return True
        except Exception as e:
            logger.warning(f"Redis health check failed: {e}")
            return False
    
    def get_health_status(self) -> dict:
        db_ok = self.check_database()
        redis_ok = self.check_redis()
        return {
            "status": "healthy" if db_ok and redis_ok else "degraded",
            "database": "ok" if db_ok else "error",
            "redis": "ok" if redis_ok else "error",
        }
