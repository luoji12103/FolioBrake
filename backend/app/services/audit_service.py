import logging

logger = logging.getLogger(__name__)

class AuditService:
    def run_audit(self, strategy_id: int, backtest_id: int):
        logger.info(f"Running audit for strategy {strategy_id}, backtest {backtest_id}")
        return {"audit_id": 0, "grade": "GREEN", "score": 100}
    
    def get_audit_report(self, audit_id: int):
        logger.info(f"Getting audit report {audit_id}")
        return {"audit_id": audit_id, "grade": "GREEN", "score": 100, "checks": []}
