import logging
from typing import Optional

logger = logging.getLogger(__name__)

class NotificationService:
    def send_alert(self, user_id: int, message: str, alert_type: str = "info"):
        logger.info(f"Alert to user {user_id}: [{alert_type}] {message}")
        return True
    
    def send_email(self, to: str, subject: str, body: str):
        logger.info(f"Email to {to}: {subject}")
        return True
