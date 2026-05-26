import logging

logger = logging.getLogger(__name__)

class DataService:
    def get_instruments(self):
        logger.info("Getting instruments")
        return []
    
    def get_bars(self, symbol: str):
        logger.info(f"Getting bars for {symbol}")
        return []
    
    def sync_data(self, symbols: list):
        logger.info(f"Syncing data for {symbols}")
        return {"synced": 0}
