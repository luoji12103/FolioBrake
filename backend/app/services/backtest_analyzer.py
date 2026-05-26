import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class BacktestAnalyzer:
    def analyze_results(self, results: Dict) -> Dict:
        logger.info("Analyzing backtest results")
        return {
            "total_return": results.get("total_return", 0),
            "sharpe_ratio": results.get("sharpe_ratio", 0),
            "max_drawdown": results.get("max_drawdown", 0),
            "win_rate": results.get("win_rate", 0),
        }
    
    def compare_strategies(self, results_a: Dict, results_b: Dict) -> Dict:
        logger.info("Comparing strategies")
        return {"winner": "A" if results_a.get("sharpe_ratio", 0) > results_b.get("sharpe_ratio", 0) else "B"}
