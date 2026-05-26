import logging

logger = logging.getLogger(__name__)

class MarketDataService:
    def get_real_time_price(self, symbol: str):
        logger.info(f"Getting real-time price for {symbol}")
        return {"symbol": symbol, "price": 0.0, "change": 0.0, "change_pct": 0.0}
    
    def get_market_status(self):
        logger.info("Getting market status")
        return {"status": "closed", "next_open": "2026-05-26 09:30:00"}
