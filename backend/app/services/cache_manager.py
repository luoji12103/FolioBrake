import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self):
        self._cache = {}
    
    def get(self, key: str) -> Optional[Any]:
        return self._cache.get(key)
    
    def set(self, key: str, value: Any, ttl: int = 300):
        self._cache[key] = {"value": value, "ttl": ttl}
    
    def delete(self, key: str):
        self._cache.pop(key, None)
    
    def clear(self):
        self._cache.clear()
