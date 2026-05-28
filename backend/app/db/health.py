from app.db.base import SessionLocal
from sqlalchemy import text

def check_database_health():
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
    finally:
        db.close()
