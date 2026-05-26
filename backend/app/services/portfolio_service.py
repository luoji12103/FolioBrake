import logging

logger = logging.getLogger(__name__)

class PortfolioService:
    def create_portfolio(self, name: str, initial_capital: float):
        logger.info(f"Creating portfolio {name} with {initial_capital}")
        return {"portfolio_id": 0, "name": name}
    
    def get_portfolio(self, portfolio_id: int):
        logger.info(f"Getting portfolio {portfolio_id}")
        return {"portfolio_id": portfolio_id, "name": "default", "initial_capital": 100000}
    
    def get_holdings(self, portfolio_id: int):
        logger.info(f"Getting holdings for {portfolio_id}")
        return []
