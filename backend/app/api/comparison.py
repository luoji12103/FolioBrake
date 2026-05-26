from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.base import get_db
from app.data.models import Instrument, DailyBar

router = APIRouter(tags=["comparison"])

@router.get("/compare")
def compare_etfs(symbols: str = Query(...), db: Session = Depends(get_db)):
    symbol_list = [s.strip() for s in symbols.split(",")]
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
