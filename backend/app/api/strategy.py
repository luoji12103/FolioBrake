from datetime import date as date_type
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.db.base import get_db
from app.strategy.models import StrategyConfig, StrategyRun, Signal, TargetPortfolio, ExplanationLog
from app.strategy.rotation import RiskAwareETFRotationV1
from app.data.models import Instrument

router = APIRouter(tags=["strategy"])


class RunRequest(BaseModel):
    as_of_date: str


class SignalOut(BaseModel):
    instrument_id: int
    symbol: str
    score: float
    rank: int
    reason: dict

    model_config = {"from_attributes": True}


@router.post("/run")
def run_strategy(req: RunRequest, db: Session = Depends(get_db)):
    config = db.execute(select(StrategyConfig).limit(1)).scalar_one_or_none()
    if not config:
        config = StrategyConfig(name="risk_aware_etf_rotation_v1", version="v1",
                                parameters={"max_holdings": 5, "max_concentration": 0.30,
                                           "min_positions": 3, "max_turnover": 0.50})
        db.add(config)
        db.flush()

    universe = list(db.execute(select(Instrument)).scalars().all())
    if not universe:
        return {"error": "No instruments in universe. Run data sync first."}

    strategy = RiskAwareETFRotationV1(db, config)
    as_of = date_type.fromisoformat(req.as_of_date)
    result = strategy.generate_signals(universe, as_of)
    return {"run_id": result["run_id"], "portfolio_count": len(result["portfolio"])}


@router.get("/signals")
def get_signals(run_id: int = Query(None), db: Session = Depends(get_db)):
    if run_id:
        sigs = list(db.execute(select(Signal).where(Signal.run_id == run_id).order_by(Signal.rank)).scalars().all())
    else:
        latest_run = db.execute(select(StrategyRun).order_by(desc(StrategyRun.id)).limit(1)).scalar_one_or_none()
        if not latest_run:
            return []
        sigs = list(db.execute(select(Signal).where(Signal.run_id == latest_run.id).order_by(Signal.rank)).scalars().all())

    result = []
    for s in sigs:
        inst = db.execute(select(Instrument).where(Instrument.id == s.instrument_id)).scalar_one_or_none()
        result.append({
            "instrument_id": s.instrument_id,
            "symbol": inst.symbol if inst else "?",
            "score": s.score,
            "rank": s.rank,
            "reason": s.reason,
        })
    return result


@router.get("/portfolio")
def get_portfolio(run_id: int = Query(None), db: Session = Depends(get_db)):
    if run_id:
        positions = list(db.execute(select(TargetPortfolio).where(TargetPortfolio.run_id == run_id)).scalars().all())
    else:
        latest_run = db.execute(select(StrategyRun).order_by(desc(StrategyRun.id)).limit(1)).scalar_one_or_none()
        if not latest_run:
            return []
        positions = list(db.execute(select(TargetPortfolio).where(TargetPortfolio.run_id == latest_run.id)).scalars().all())

    result = []
    for p in positions:
        inst = db.execute(select(Instrument).where(Instrument.id == p.instrument_id)).scalar_one_or_none()
        result.append({
            "instrument_id": p.instrument_id,
            "symbol": inst.symbol if inst else "?",
            "target_weight": p.target_weight,
            "score": p.score,
            "constraint_info": p.constraint_info,
        })
    return result


@router.get("/explanations/{run_id}")
def get_explanations(run_id: int, db: Session = Depends(get_db)):
    logs = list(db.execute(select(ExplanationLog).where(ExplanationLog.run_id == run_id)).scalars().all())
    return [
        {"instrument_id": l.instrument_id, "action": l.action, "reason": l.reason,
         "score_breakdown": l.score_breakdown}
        for l in logs
    ]
