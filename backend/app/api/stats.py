from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.base import get_db
from app.data.models import Instrument, DailyBar
from app.strategy.models import Signal

router = APIRouter(tags=["stats"])

@router.get("/statistics")
def get_statistics(db: Session = Depends(get_db)):
    instruments_count = db.execute(func.count(Instrument.id)).scalar()
    bars_count = db.execute(func.count(DailyBar.id)).scalar()
    signals_count = db.execute(func.count(Signal.id)).scalar()
    
    return {
        "instruments": instruments_count,
        "daily_bars": bars_count,
        "signals": signals_count,
    }
