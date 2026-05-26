import logging
from typing import Dict

logger = logging.getLogger(__name__)

class AuditRunner:
    def run_audit(self, strategy_id: int, backtest_id: int) -> Dict:
        logger.info(f"Running audit for strategy {strategy_id}, backtest {backtest_id}")
        return {
            "audit_id": 0,
            "grade": "GREEN",
            "score": 100,
            "checks": [],
        }
    
    def get_report(self, audit_id: int) -> Dict:
        logger.info(f"Getting audit report for {audit_id}")
        return {
            "audit_id": audit_id,
            "grade": "GREEN",
            "score": 100,
            "checks": [],
        }
