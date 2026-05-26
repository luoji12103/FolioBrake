import logging
from typing import Any, List

logger = logging.getLogger(__name__)

class ValidationService:
    def validate_instrument(self, symbol: str) -> bool:
        return len(symbol) == 6 and symbol.isdigit()
    
    def validate_date(self, date_str: str) -> bool:
        try:
            from datetime import datetime
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False
    
    def validate_amount(self, amount: float) -> bool:
        return amount > 0
