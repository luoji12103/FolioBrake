import logging
from typing import Dict

logger = logging.getLogger(__name__)

class BacktestRunner:
    def run_backtest(self, config: Dict) -> Dict:
        logger.info(f"Running backtest with config: {config}")
        return {
            "run_id": 0,
            "status": "completed",
            "metrics": {
                "total_return": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
            },
        }
    
    def get_status(self, run_id: int) -> Dict:
        logger.info(f"Getting backtest status for {run_id}")
        return {"run_id": run_id, "status": "completed"}
