from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.db.base import get_db
from app.data.models import Instrument, DailyBar

router = APIRouter(tags=["sector"])

@router.get("/sectors")
def get_sectors(db: Session = Depends(get_db)):
    sectors = db.execute(select(Instrument.category, func.count(Instrument.id)).group_by(Instrument.category)).all()
    return {"sectors": [{"name": s[0] or "Unknown", "count": s[1]} for s in sectors]}
