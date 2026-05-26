import logging

logger = logging.getLogger(__name__)

class StrategyService:
    def run_strategy(self, config_id: int):
        logger.info(f"Running strategy {config_id}")
        return {"run_id": 0, "status": "completed"}
    
    def get_signals(self, run_id: int):
        logger.info(f"Getting signals for run {run_id}")
        return []
