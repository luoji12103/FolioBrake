from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DataLineage:
    def __init__(self):
        self.records = []
    
    def track(self, source: str, symbol: str, record_count: int):
        self.records.append({
            "source": source,
            "symbol": symbol,
            "record_count": record_count,
            "timestamp": datetime.now().isoformat(),
        })
        logger.info(f"Data lineage: {source} - {symbol} - {record_count} records")
