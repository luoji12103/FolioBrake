from sqlalchemy.orm import Session
from sqlalchemy import text

def optimize_query(db: Session, query: str, params: dict = None):
    result = db.execute(text(query), params or {})
    return result.fetchall()

def explain_query(db: Session, query: str):
    result = db.execute(text(f"EXPLAIN ANALYZE {query}"))
    return [row[0] for row in result.fetchall()]
