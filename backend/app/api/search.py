from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, select
from app.db.base import get_db
from app.data.models import Instrument

router = APIRouter(tags=["search"])


def _escape_like(value: str) -> str:
    """Escape SQL LIKE wildcard characters in user input."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


@router.get("/search")
def search(q: str = Query(..., min_length=1, max_length=100), db: Session = Depends(get_db)):
    pattern = f"%{_escape_like(q)}%"
    results = db.execute(
        select(Instrument).where(
            or_(
                Instrument.symbol.ilike(pattern, escape="\\"),
                Instrument.name.ilike(pattern, escape="\\"),
            )
        ).limit(20)
    ).scalars().all()

    return {
        "query": q,
        "results": [
            {"id": i.id, "symbol": i.symbol, "name": i.name}
            for i in results
        ],
        "total": len(results),
    }
