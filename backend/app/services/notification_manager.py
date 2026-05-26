import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class NotificationManager:
    def __init__(self):
        self._notifications: List[Dict[str, Any]] = []
    
    def add_notification(self, user_id: int, message: str, notification_type: str = "info"):
        notification = {
            "user_id": user_id,
            "message": message,
            "type": notification_type,
            "read": False,
        }
        self._notifications.append(notification)
        logger.info(f"Notification added for user {user_id}: {message}")
    
    def get_notifications(self, user_id: int) -> List[Dict[str, Any]]:
        return [n for n in self._notifications if n["user_id"] == user_id]
    
    def mark_read(self, user_id: int, index: int):
        user_notifications = self.get_notifications(user_id)
        if 0 <= index < len(user_notifications):
            user_notifications[index]["read"] = True
