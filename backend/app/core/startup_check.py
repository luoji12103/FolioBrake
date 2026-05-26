from app.db.base import SessionLocal
from sqlalchemy import text

def check_database():
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except:
        return False

def check_redis():
    try:
        import redis
        r = redis.Redis(host="redis", port=6379, socket_connect_timeout=2)
        r.ping()
        return True
    except:
        return False
