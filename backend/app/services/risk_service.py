import logging

logger = logging.getLogger(__name__)

class RiskService:
    def get_risk_state(self):
        logger.info("Getting risk state")
        return {"state": "NORMAL", "transition_reason": "default"}
    
    def get_risk_alerts(self):
        logger.info("Getting risk alerts")
        return {"alerts": [], "unread_count": 0}
    
    def create_alert(self, alert_type: str, severity: str, title: str, message: str):
        logger.info(f"Creating alert: {title}")
        return True
