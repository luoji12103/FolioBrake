from datetime import date as date_type
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.db.base import get_db
from app.backtest.models import BacktestConfig, BacktestRun, PortfolioSnapshot, SimulatedTrade, PerformanceMetric
from app.backtest.engine import BacktestEngine

router = APIRouter(tags=["backtest"])


class BacktestConfigRequest(BaseModel):
    strategy_config_id: int = 1
    start_date: str
    end_date: str
    initial_capital: float = 100000.0
    benchmark_symbol: str = "510050"


@router.post("/run")
def run_backtest(req: BacktestConfigRequest, db: Session = Depends(get_db)):
    config = BacktestConfig(
        strategy_config_id=req.strategy_config_id,
        start_date=date_type.fromisoformat(req.start_date),
        end_date=date_type.fromisoformat(req.end_date),
        initial_capital=req.initial_capital,
        cost_model={"commission": 0.0003, "slippage": 0.001},
        benchmark_symbol=req.benchmark_symbol,
    )
    db.add(config)
    db.flush()

    engine = BacktestEngine(db)
    run = engine.run(config)
    return {"run_id": run.id, "status": run.status, "config_hash": run.config_hash}


@router.get("/status/{run_id}")
def get_status(run_id: int, db: Session = Depends(get_db)):
    run = db.execute(select(BacktestRun).where(BacktestRun.id == run_id)).scalar_one_or_none()
    if not run:
        return {"error": "Run not found"}
    return {"run_id": run.id, "status": run.status, "config_hash": run.config_hash,
            "started_at": str(run.started_at), "completed_at": str(run.completed_at) if run.completed_at else None}


@router.get("/results/{run_id}")
def get_results(run_id: int, db: Session = Depends(get_db)):
    run = db.execute(select(BacktestRun).where(BacktestRun.id == run_id)).scalar_one_or_none()
    if not run:
        return {"error": "Run not found"}

    snapshots = list(db.execute(
        select(PortfolioSnapshot).where(PortfolioSnapshot.run_id == run_id).order_by(PortfolioSnapshot.date)
    ).scalars().all())
    equity_curve = [{"date": str(s.date), "total_value": s.total_value, "daily_return": s.daily_return} for s in snapshots]

    metrics = list(db.execute(
        select(PerformanceMetric).where(PerformanceMetric.run_id == run_id)
    ).scalars().all())
    metrics_dict = {m.metric_name: m.value for m in metrics}

    trades = list(db.execute(
        select(SimulatedTrade).where(SimulatedTrade.run_id == run_id).order_by(SimulatedTrade.date)
    ).scalars().all())
    trade_list = [{"date": str(t.date), "instrument_id": t.instrument_id, "side": t.side,
                   "quantity": t.quantity, "price": t.price, "slippage": t.slippage,
                   "commission": t.commission} for t in trades]

    return {"run_id": run.id, "equity_curve": equity_curve, "metrics": metrics_dict, "trades": trade_list}


@router.get("/compare/{run_id}")
def compare_benchmark(run_id: int, db: Session = Depends(get_db)):
    return {"run_id": run_id, "note": "Benchmark comparison available after Phase 9 reports"}
