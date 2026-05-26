import logging

logger = logging.getLogger(__name__)

class ReportingService:
    def generate_report(self, report_type: str, params: dict):
        logger.info(f"Generating report: {report_type}")
        return {"report_id": 0, "status": "generated", "url": "/reports/0.pdf"}
    
    def get_report(self, report_id: int):
        logger.info(f"Getting report {report_id}")
        return {"report_id": report_id, "status": "ready", "content": ""}
