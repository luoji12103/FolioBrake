import logging

logger = logging.getLogger(__name__)

class AnalysisService:
    def compute_drawdown(self, symbol: str):
        logger.info(f"Computing drawdown for {symbol}")
        return {"symbol": symbol, "max_drawdown": 0.0}
    
    def compute_var(self, symbol: str):
        logger.info(f"Computing VaR for {symbol}")
        return {"symbol": symbol, "var_95": 0.0}
    
    def compute_correlation(self, symbols: list):
        logger.info(f"Computing correlation for {symbols}")
        return {"symbols": symbols, "matrix": []}
