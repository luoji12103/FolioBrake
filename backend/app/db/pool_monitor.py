from sqlalchemy import event
from app.db.base import engine
import logging

logger = logging.getLogger(__name__)

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_connection, connection_rec, connection_proxy):
    logger.debug("Connection checked out from pool")

@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_connection, connection_rec):
    logger.debug("Connection returned to pool")

def get_pool_status():
    pool = engine.pool
    return {
        "size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
    }
