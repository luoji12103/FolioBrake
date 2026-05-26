import logging

logger = logging.getLogger(__name__)

def send_notification(user_id: int, message: str, type: str = "info"):
    logger.info(f"Notification to user {user_id}: {message}")
    return True
