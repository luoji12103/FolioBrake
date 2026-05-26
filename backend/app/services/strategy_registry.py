import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class StrategyRegistry:
    def __init__(self):
        self._strategies: Dict[str, Dict[str, Any]] = {}
    
    def register_strategy(self, name: str, strategy_type: str, params: Dict = None):
        self._strategies[name] = {
            "type": strategy_type,
            "params": params or {},
            "status": "active",
        }
        logger.info(f"Registered strategy: {name}")
    
    def get_strategy(self, name: str) -> Dict:
        return self._strategies.get(name, {})
    
    def list_strategies(self) -> List[str]:
        return list(self._strategies.keys())
