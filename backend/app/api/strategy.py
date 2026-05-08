from datetime import date as date_type
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.db.base import get_db
from app.strategy.models import StrategyConfig, StrategyRun, Signal, TargetPortfolio, ExplanationLog
from app.strategy.rotation import RiskAwareETFRotationV1
from app.data.models import Instrument
from app.risk.models import RiskStateRecord

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

    # Evaluate risk state and scale exposure
    from app.risk.daily_check import get_risk_scale
    risk_scale = get_risk_scale(db, as_of)
    risk_state = db.execute(
        select(RiskStateRecord).order_by(desc(RiskStateRecord.date)).limit(1)
    ).scalar_one_or_none()

    result = strategy.generate_signals(universe, as_of)

    # Apply risk scaling to portfolio weights
    if risk_scale < 1.0 and "portfolio" in result:
        for p in result["portfolio"]:
            p["target_weight"] *= risk_scale

    db.commit()
    return {
        "run_id": result["run_id"],
        "portfolio_count": len(result.get("portfolio", [])),
        "risk_state": risk_state.state if risk_state else "NORMAL",
        "risk_scale": risk_scale,
    }


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


@router.get("/sector-breakdown")
def sector_breakdown(run_id: int = Query(None), db: Session = Depends(get_db)):
    """Return portfolio exposure by ETF category/sector."""
    if run_id:
        positions = list(db.execute(
            select(TargetPortfolio).where(TargetPortfolio.run_id == run_id)
        ).scalars().all())
    else:
        latest_run = db.execute(
            select(StrategyRun).order_by(desc(StrategyRun.id)).limit(1)
        ).scalar_one_or_none()
        if not latest_run:
            return {"sectors": [], "note": "No strategy run yet"}
        positions = list(db.execute(
            select(TargetPortfolio).where(TargetPortfolio.run_id == latest_run.id)
        ).scalars().all())

    instruments = {i.id: i for i in db.execute(select(Instrument)).scalars().all()}
    sectors: dict[str, float] = {}
    for p in positions:
        inst = instruments.get(p.instrument_id)
        cat = inst.category if inst and inst.category else "uncategorized"
        sectors[cat] = sectors.get(cat, 0.0) + p.target_weight

    return {
        "sectors": [{"category": k, "weight": round(v, 4)} for k, v in sectors.items()],
        "run_id": run_id,
    }


@router.get("/signal-history")
def get_signal_history(
    limit: int = Query(50),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    """Return historical signals with subsequent performance and accuracy stats."""
    from app.data.models import DailyBar

    rows = list(
        db.execute(
            select(Signal, StrategyRun, Instrument)
            .join(StrategyRun, Signal.run_id == StrategyRun.id)
            .join(Instrument, Signal.instrument_id == Instrument.id)
            .order_by(StrategyRun.run_date.desc(), Signal.rank)
            .offset(offset)
            .limit(limit)
        ).all()
    )

    result = []
    for sig, run, inst in rows:
        signal_date = run.run_date

        base_bar = (
            db.execute(
                select(DailyBar)
                .where(
                    DailyBar.instrument_id == sig.instrument_id,
                    DailyBar.trade_date <= signal_date,
                )
                .order_by(DailyBar.trade_date.desc())
                .limit(1)
            )
            .scalars()
            .first()
        )
        if not base_bar:
            continue

        base_close = base_bar.close
        base_date = base_bar.trade_date

        def _return_after(days: int) -> float | None:
            from datetime import timedelta

            target = base_date + timedelta(days=days)
            bar = (
                db.execute(
                    select(DailyBar)
                    .where(
                        DailyBar.instrument_id == sig.instrument_id,
                        DailyBar.trade_date >= target,
                    )
                    .order_by(DailyBar.trade_date.asc())
                    .limit(1)
                )
                .scalars()
                .first()
            )
            if bar and base_close:
                return round((bar.close - base_close) / base_close, 6)
            return None

        ret_7d = _return_after(7)
        ret_30d = _return_after(30)

        result.append(
            {
                "id": sig.id,
                "date": str(signal_date),
                "instrument_id": sig.instrument_id,
                "symbol": inst.symbol,
                "score": sig.score,
                "rank": sig.rank,
                "reason": sig.reason or {},
                "subsequent_return_7d": ret_7d,
                "subsequent_return_30d": ret_30d,
                "is_correct_7d": ret_7d is not None and ret_7d > 0,
            }
        )

    total = len(result)
    valid_7d = [s for s in result if s["subsequent_return_7d"] is not None]
    valid_30d = [s for s in result if s["subsequent_return_30d"] is not None]
    correct_7d = sum(1 for s in valid_7d if s["subsequent_return_7d"] > 0)
    correct_30d = sum(1 for s in valid_30d if s["subsequent_return_30d"] > 0)

    return {
        "signals": result,
        "statistics": {
            "total_signals": total,
            "accuracy_7d": round(correct_7d / len(valid_7d), 4) if valid_7d else 0,
            "accuracy_30d": round(correct_30d / len(valid_30d), 4) if valid_30d else 0,
            "avg_return_7d": round(sum(s["subsequent_return_7d"] for s in valid_7d) / len(valid_7d), 6) if valid_7d else 0,
            "avg_return_30d": round(sum(s["subsequent_return_30d"] for s in valid_30d) / len(valid_30d), 6) if valid_30d else 0,
        },
    }


class ConfigCreateRequest(BaseModel):
    name: str
    version: str = "v1"
    parameters: dict = {}
    universe_filter: dict = {}
    risk_profile: str = "balanced"


class ConfigUpdateRequest(BaseModel):
    name: str | None = None
    version: str | None = None
    parameters: dict | None = None
    universe_filter: dict | None = None
    risk_profile: str | None = None


@router.get("/configs")
def list_configs(db: Session = Depends(get_db)):
    """List all strategy configurations."""
    configs = list(db.execute(select(StrategyConfig).order_by(StrategyConfig.id)).scalars().all())
    return [
        {
            "id": c.id,
            "name": c.name,
            "version": c.version,
            "parameters": c.parameters,
            "universe_filter": c.universe_filter,
            "risk_profile": c.risk_profile,
            "created_at": str(c.created_at) if c.created_at else None,
        }
        for c in configs
    ]


@router.post("/configs")
def create_config(req: ConfigCreateRequest, db: Session = Depends(get_db)):
    """Create a new strategy configuration."""
    config = StrategyConfig(
        name=req.name,
        version=req.version,
        parameters=req.parameters,
        universe_filter=req.universe_filter,
        risk_profile=req.risk_profile,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return {
        "id": config.id,
        "name": config.name,
        "version": config.version,
        "parameters": config.parameters,
        "universe_filter": config.universe_filter,
        "risk_profile": config.risk_profile,
        "created_at": str(config.created_at) if config.created_at else None,
    }


@router.get("/configs/{config_id}")
def get_config(config_id: int, db: Session = Depends(get_db)):
    """Get a single strategy configuration."""
    config = db.execute(
        select(StrategyConfig).where(StrategyConfig.id == config_id)
    ).scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    return {
        "id": config.id,
        "name": config.name,
        "version": config.version,
        "parameters": config.parameters,
        "universe_filter": config.universe_filter,
        "risk_profile": config.risk_profile,
        "created_at": str(config.created_at) if config.created_at else None,
    }


@router.put("/configs/{config_id}")
def update_config(config_id: int, req: ConfigUpdateRequest, db: Session = Depends(get_db)):
    """Update strategy configuration fields."""
    config = db.execute(
        select(StrategyConfig).where(StrategyConfig.id == config_id)
    ).scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")

    if req.name is not None:
        config.name = req.name
    if req.version is not None:
        config.version = req.version
    if req.parameters is not None:
        config.parameters = req.parameters
    if req.universe_filter is not None:
        config.universe_filter = req.universe_filter
    if req.risk_profile is not None:
        config.risk_profile = req.risk_profile

    db.commit()
    db.refresh(config)
    return {
        "id": config.id,
        "name": config.name,
        "version": config.version,
        "parameters": config.parameters,
        "universe_filter": config.universe_filter,
        "risk_profile": config.risk_profile,
        "created_at": str(config.created_at) if config.created_at else None,
    }


@router.delete("/configs/{config_id}")
def delete_config(config_id: int, db: Session = Depends(get_db)):
    """Delete a strategy configuration."""
    config = db.execute(
        select(StrategyConfig).where(StrategyConfig.id == config_id)
    ).scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")

    runs_count = db.execute(
        select(StrategyRun).where(StrategyRun.config_id == config_id).limit(1)
    ).scalar_one_or_none()
    if runs_count:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete config: strategy runs reference it. Archive instead.",
        )

    db.delete(config)
    db.commit()
    return {"ok": True}
