import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class StrategyAnalyzer:
    def analyze_strategy(self, strategy_id: int) -> Dict:
        logger.info(f"Analyzing strategy {strategy_id}")
        return {
            "strategy_id": strategy_id,
            "total_signals": 0,
            "avg_score": 0,
            "win_rate": 0,
        }
    
    def compare_strategies(self, strategy_ids: List[int]) -> Dict:
        logger.info(f"Comparing strategies {strategy_ids}")
        return {"best_strategy": strategy_ids[0] if strategy_ids else None}
