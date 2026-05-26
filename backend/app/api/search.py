from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.db.base import get_db
from app.data.models import Instrument

router = APIRouter(tags=["search"])

@router.get("/search")
def search(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    results = db.execute(
        select(Instrument).where(
            or_(
                Instrument.symbol.ilike(f"%{q}%"),
                Instrument.name.ilike(f"%{q}%"),
            )
        ).limit(20)
    ).scalars().all()
    
    return {
        "query": q,
        "results": [
            {"id": i.id, "symbol": i.symbol, "name": i.name}
            for i in results
        ],
        "total": len(results)
    }
