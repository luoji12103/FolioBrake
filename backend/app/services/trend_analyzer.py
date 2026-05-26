import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class TrendAnalyzer:
    def analyze_trend(self, prices: List[float], period: int = 20) -> Dict:
        if len(prices) < period:
            return {"trend": "insufficient_data", "strength": 0}
        
        recent = prices[-period:]
        change = (recent[-1] - recent[0]) / recent[0] if recent[0] != 0 else 0
        
        if change > 0.05:
            return {"trend": "bullish", "strength": min(change * 10, 1.0)}
        elif change < -0.05:
            return {"trend": "bearish", "strength": min(abs(change) * 10, 1.0)}
        return {"trend": "neutral", "strength": 0.5}
