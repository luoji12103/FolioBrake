import logging
import time

logger = logging.getLogger(__name__)

class MetricsService:
    def __init__(self):
        self._metrics = {}
    
    def record_metric(self, name: str, value: float, tags: dict = None):
        self._metrics[name] = {"value": value, "tags": tags, "timestamp": time.time()}
        logger.debug(f"Metric: {name}={value}")
    
    def get_metric(self, name: str):
        return self._metrics.get(name)
    
    def get_all_metrics(self):
        return self._metrics
