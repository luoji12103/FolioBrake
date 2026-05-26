import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class PaperTradingEngine:
    def create_portfolio(self, name: str, initial_capital: float) -> Dict:
        logger.info(f"Creating portfolio {name} with {initial_capital}")
        return {"portfolio_id": 0, "name": name, "initial_capital": initial_capital}
    
    def apply_signal(self, portfolio_id: int, signal_date: str, target_weights: Dict[str, float]) -> List[Dict]:
        logger.info(f"Applying signal to portfolio {portfolio_id}")
        return []
    
    def get_pnl(self, portfolio_id: int) -> Dict:
        logger.info(f"Getting PnL for portfolio {portfolio_id}")
        return {
            "total_value": 0.0,
            "cash": 0.0,
            "invested": 0.0,
            "total_pnl": 0.0,
            "total_pnl_pct": 0.0,
        }
