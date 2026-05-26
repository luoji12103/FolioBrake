import logging

logger = logging.getLogger(__name__)

class ExportService:
    def export_csv(self, data: list, filename: str):
        logger.info(f"Exporting CSV: {filename}")
        return {"filename": filename, "status": "exported"}
    
    def export_json(self, data: list, filename: str):
        logger.info(f"Exporting JSON: {filename}")
        return {"filename": filename, "status": "exported"}
    
    def export_pdf(self, data: dict, filename: str):
        logger.info(f"Exporting PDF: {filename}")
        return {"filename": filename, "status": "exported"}
