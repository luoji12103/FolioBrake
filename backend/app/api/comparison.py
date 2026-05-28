from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.base import get_db
from app.data.models import Instrument, DailyBar

router = APIRouter(tags=["comparison"])

MAX_COMPARE_SYMBOLS = 10


@router.get("/compare")
def compare_etfs(
    symbols: str = Query(..., max_length=200),
    db: Session = Depends(get_db),
):
    symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]
    if len(symbol_list) > MAX_COMPARE_SYMBOLS:
        raise HTTPException(status_code=400, detail=f"Maximum {MAX_COMPARE_SYMBOLS} symbols allowed")
    if not symbol_list:
        raise HTTPException(status_code=400, detail="At least one symbol required")

    results = []
    for symbol in symbol_list:
        inst = db.execute(select(Instrument).where(Instrument.symbol == symbol)).scalar_one_or_none()
        if not inst:
            continue
        bars = list(db.execute(select(DailyBar).where(DailyBar.instrument_id == inst.id).order_by(DailyBar.trade_date.desc()).limit(30)).scalars().all())
        if bars:
            returns = [(bars[i].close - bars[i+1].close) / bars[i+1].close for i in range(len(bars)-1)]
            results.append({
                "symbol": symbol,
                "name": inst.name,
                "latest_price": bars[0].close,
                "avg_return": sum(returns) / len(returns) if returns else 0,
                "volatility": (sum(r**2 for r in returns) / len(returns))**0.5 if returns else 0,
            })
    return {"comparison": results}
