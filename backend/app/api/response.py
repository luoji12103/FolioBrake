from pydantic import BaseModel
from typing import Any, Optional

class ApiResponse(BaseModel):
    success: bool = True
    data: Any = None
    error: Optional[str] = None
    message: Optional[str] = None

def success_response(data: Any, message: str = "Success") -> dict:
    return {"success": True, "data": data, "message": message}

def error_response(error: str, message: str = "Error") -> dict:
    return {"success": False, "error": error, "message": message}
