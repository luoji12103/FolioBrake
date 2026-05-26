from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.base import get_db

router = APIRouter(tags=["export"])

@router.get("/export/{symbol}")
def export_data(symbol: str, format: str = Query("csv"), db: Session = Depends(get_db)):
    import csv, io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["date", "open", "high", "low", "close", "volume"])
    output.seek(0)
    return StreamingResponse(io.BytesIO(output.getvalue().encode()), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={symbol}.csv"})
