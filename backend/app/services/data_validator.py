import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class DataValidator:
    def validate_bar(self, bar: Dict[str, Any]) -> bool:
        required = ["trade_date", "open", "high", "low", "close", "volume"]
        return all(k in bar for k in required)
    
    def validate_instrument(self, instrument: Dict[str, Any]) -> bool:
        required = ["symbol", "name"]
        return all(k in instrument for k in required)
    
    def validate_signal(self, signal: Dict[str, Any]) -> bool:
        required = ["instrument_id", "score", "rank"]
        return all(k in signal for k in required)
