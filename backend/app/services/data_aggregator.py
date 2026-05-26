import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class DataAggregator:
    def aggregate_bars(self, bars: List[Dict], period: str = "weekly") -> List[Dict]:
        logger.info(f"Aggregating {len(bars)} bars to {period}")
        return bars
    
    def aggregate_signals(self, signals: List[Dict]) -> Dict:
        logger.info(f"Aggregating {len(signals)} signals")
        return {
            "total": len(signals),
            "avg_score": sum(s.get("score", 0) for s in signals) / len(signals) if signals else 0,
        }
