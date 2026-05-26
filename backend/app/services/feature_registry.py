import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class FeatureRegistry:
    def __init__(self):
        self._features: Dict[str, Dict[str, Any]] = {}
    
    def register_feature(self, name: str, category: str, lookback: int, params: Dict = None):
        self._features[name] = {
            "category": category,
            "lookback": lookback,
            "params": params or {},
        }
        logger.info(f"Registered feature: {name}")
    
    def get_feature(self, name: str) -> Dict:
        return self._features.get(name, {})
    
    def list_features(self) -> List[str]:
        return list(self._features.keys())
    
    def list_by_category(self, category: str) -> List[str]:
        return [name for name, f in self._features.items() if f["category"] == category]
