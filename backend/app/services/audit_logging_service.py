import logging

logger = logging.getLogger(__name__)

class AuditLoggingService:
    def log_action(self, user_id: int, action: str, resource: str, details: dict = None):
        logger.info(f"Audit: user={user_id} action={action} resource={resource} details={details}")
    
    def get_audit_trail(self, user_id: int = None, resource: str = None):
        logger.info(f"Getting audit trail: user={user_id} resource={resource}")
        return []
