import logging
import numpy as np
from typing import List

logger = logging.getLogger(__name__)

class RiskCalculator:
    def calculate_var(self, returns: List[float], confidence: float = 0.95) -> float:
        return float(np.percentile(returns, (1 - confidence) * 100))
    
    def calculate_cvar(self, returns: List[float], confidence: float = 0.95) -> float:
        var = self.calculate_var(returns, confidence)
        return float(np.mean([r for r in returns if r <= var]))
    
    def calculate_sharpe(self, returns: List[float], risk_free_rate: float = 0.03) -> float:
        excess_returns = np.array(returns) - risk_free_rate / 252
        return float(np.mean(excess_returns) / np.std(excess_returns)) if np.std(excess_returns) > 0 else 0.0
