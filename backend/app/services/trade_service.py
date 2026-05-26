import logging

logger = logging.getLogger(__name__)

class TradeService:
    def execute_trade(self, portfolio_id: int, instrument_id: int, side: str, quantity: float, price: float):
        logger.info(f"Executing trade: {side} {quantity} of {instrument_id} at {price}")
        return {"trade_id": 0, "status": "executed"}
    
    def get_trade_history(self, portfolio_id: int):
        logger.info(f"Getting trade history for {portfolio_id}")
        return []
