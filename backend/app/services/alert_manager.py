import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class AlertManager:
    def __init__(self):
        self._alerts: List[Dict[str, Any]] = []
    
    def create_alert(self, alert_type: str, severity: str, title: str, message: str):
        alert = {
            "type": alert_type,
            "severity": severity,
            "title": title,
            "message": message,
            "read": False,
        }
        self._alerts.append(alert)
        logger.warning(f"Alert: [{severity}] {title} - {message}")
    
    def get_alerts(self, unread_only: bool = False) -> List[Dict[str, Any]]:
        if unread_only:
            return [a for a in self._alerts if not a["read"]]
        return self._alerts
    
    def mark_read(self, index: int):
        if 0 <= index < len(self._alerts):
            self._alerts[index]["read"] = True
