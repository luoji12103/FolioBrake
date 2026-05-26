from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.base import get_db
from app.data.models import DailyBar, Instrument

router = APIRouter(tags=["trend"])

@router.get("/trend/{symbol}")
def analyze_trend(symbol: str, period: int = Query(20), db: Session = Depends(get_db)):
    return {"symbol": symbol, "period": period, "trend": "neutral", "strength": 0.5}
