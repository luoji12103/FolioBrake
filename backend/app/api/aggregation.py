from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.db.base import get_db
from app.data.models import DailyBar

router = APIRouter(tags=["aggregation"])

VALID_PERIODS = {"daily", "weekly", "monthly", "quarterly", "yearly"}


@router.get("/aggregate/{symbol}")
def aggregate_data(
    symbol: str,
    period: str = Query("daily", enum=list(VALID_PERIODS)),
    db: Session = Depends(get_db),
):
    return {"symbol": symbol, "period": period, "data": []}
