import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

class ResultFormatter:
    def format_success(self, data: Any, message: str = "Success") -> Dict:
        return {"success": True, "data": data, "message": message}
    
    def format_error(self, error: str, message: str = "Error") -> Dict:
        return {"success": False, "error": error, "message": message}
    
    def format_paginated(self, items: list, total: int, page: int, page_size: int) -> Dict:
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
        }
