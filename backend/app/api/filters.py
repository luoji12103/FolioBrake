from typing import Optional
from pydantic import BaseModel

class FilterParams(BaseModel):
    search: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
