import re

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.auth import verify_api_key
from app.db.base import get_db

router = APIRouter(tags=["export"])

ALLOWED_EXPORT_FORMATS = {"csv", "json"}
_SAFE_FILENAME = re.compile(r'^[a-zA-Z0-9_\-]+$')


@router.get("/export/{symbol}")
def export_data(
    symbol: str,
    format: str = Query("csv", enum=list(ALLOWED_EXPORT_FORMATS)),
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    if len(symbol) > 20:
        raise HTTPException(status_code=400, detail="Symbol too long")
    safe_name = symbol if _SAFE_FILENAME.match(symbol) else "export"
    import csv, io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["date", "open", "high", "low", "close", "volume"])
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={safe_name}.csv"},
    )
