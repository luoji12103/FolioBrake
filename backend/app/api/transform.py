from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.base import get_db

router = APIRouter(tags=["transform"])

@router.get("/transform/{symbol}")
def transform_data(symbol: str, period: str = Query("daily"), db: Session = Depends(get_db)):
    return {"symbol": symbol, "period": period, "transformed": True}
