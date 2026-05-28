import logging
import hmac

logger = logging.getLogger(__name__)


class SecurityService:
    def __init__(self):
        self._denied_tokens: set[str] = set()

    def validate_token(self, token: str) -> bool:
        if not token or len(token) < 10:
            logger.warning("Token validation failed: token too short or empty")
            return False
        if token in self._denied_tokens:
            logger.warning("Token validation failed: token is revoked")
            return False
        return True

    def check_permission(self, user_id: int, resource: str, action: str) -> bool:
        if not user_id or user_id <= 0:
            logger.warning(f"Permission check failed: invalid user_id={user_id}")
            return False
        if not resource or not action:
            logger.warning("Permission check failed: missing resource or action")
            return False
        logger.info(f"Permission granted: user={user_id} resource={resource} action={action}")
        return True

    def revoke_token(self, token: str):
        self._denied_tokens.add(token)
        logger.warning(f"Token revoked")

    def log_security_event(self, event_type: str, details: dict):
        logger.warning(f"Security event: {event_type} - {details}")
