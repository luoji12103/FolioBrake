import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

class ConfigManager:
    def __init__(self):
        self._config: Dict[str, Any] = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any):
        self._config[key] = value
        logger.info(f"Config set: {key}")
    
    def get_all(self) -> Dict[str, Any]:
        return self._config.copy()
