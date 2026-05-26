import logging

logger = logging.getLogger(__name__)

class DataSyncService:
    def sync_instruments(self):
        logger.info("Syncing instruments")
        return {"synced": 0}
    
    def sync_bars(self, symbol: str):
        logger.info(f"Syncing bars for {symbol}")
        return {"synced": 0}
