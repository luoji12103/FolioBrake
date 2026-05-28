import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class DataProcessor:
    def process_bars(self, bars: List[Dict]) -> List[Dict]:
        logger.info(f"Processing {len(bars)} bars")
        return bars
    
    def calculate_returns(self, prices: List[float]) -> List[float]:
        if len(prices) < 2:
            return []
        return [(prices[i] - prices[i-1]) / prices[i-1] if prices[i-1] != 0 else 0.0
                for i in range(1, len(prices))]
    
    def normalize_data(self, data: List[float]) -> List[float]:
        if not data:
            return []
        min_val = min(data)
        max_val = max(data)
        range_val = max_val - min_val
        return [(x - min_val) / range_val if range_val > 0 else 0 for x in data]
