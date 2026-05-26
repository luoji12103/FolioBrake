from pydantic import BaseModel, validator
from typing import Optional

class DateRange(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    @validator("start_date", "end_date")
    def validate_date(cls, v):
        if v is not None:
            try:
                from datetime import datetime
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format")
        return v
