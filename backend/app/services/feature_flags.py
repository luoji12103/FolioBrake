import logging
from typing import Dict

logger = logging.getLogger(__name__)

class FeatureFlags:
    def __init__(self):
        self._flags: Dict[str, bool] = {}
    
    def is_enabled(self, flag: str) -> bool:
        return self._flags.get(flag, False)
    
    def enable(self, flag: str):
        self._flags[flag] = True
        logger.info(f"Feature enabled: {flag}")
    
    def disable(self, flag: str):
        self._flags[flag] = False
        logger.info(f"Feature disabled: {flag}")
