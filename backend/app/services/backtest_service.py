import logging

logger = logging.getLogger(__name__)

class BacktestService:
    def run_backtest(self, config_id: int):
        logger.info(f"Running backtest {config_id}")
        return {"run_id": 0, "status": "completed"}
    
    def get_results(self, run_id: int):
        logger.info(f"Getting backtest results {run_id}")
        return {"run_id": run_id, "metrics": {}, "equity_curve": []}
