import logging

logger = logging.getLogger(__name__)

class LoggingService:
    def log_event(self, event_type: str, message: str, level: str = "info"):
        getattr(logger, level, logger.info)(f"[{event_type}] {message}")
    
    def log_error(self, error: Exception, context: str = ""):
        logger.error(f"Error in {context}: {error}")
    
    def log_audit(self, user_id: int, action: str, resource: str):
        logger.info(f"Audit: user={user_id} action={action} resource={resource}")
