import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class DataSourceManager:
    def __init__(self):
        self._sources: Dict[str, Dict] = {}
    
    def register_source(self, name: str, source_type: str, config: Dict):
        self._sources[name] = {"type": source_type, "config": config, "status": "active"}
        logger.info(f"Registered data source: {name}")
    
    def get_source(self, name: str) -> Dict:
        return self._sources.get(name, {})
    
    def list_sources(self) -> List[str]:
        return list(self._sources.keys())
    
    def check_health(self, name: str) -> str:
        source = self._sources.get(name)
        return source.get("status", "unknown") if source else "not_found"
