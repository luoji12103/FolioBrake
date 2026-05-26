from sqlalchemy import event
from app.db.base import engine
import time
import logging

logger = logging.getLogger(__name__)

@event.listens_for(engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault("query_start_time", []).append(time.time())

@event.listens_for(engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info["query_start_time"].pop(-1)
    if total > 0.5:  # Log slow queries (>500ms)
        logger.warning(f"Slow query ({total:.3f}s): {statement[:200]}")
