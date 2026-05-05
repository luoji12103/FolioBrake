from datetime import date as date_type
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.db.base import get_db
from app.strategy.models import StrategyConfig
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
    # Look up or create strategy config
    strat_cfg = db.execute(
        select(StrategyConfig).where(StrategyConfig.id == req.strategy_config_id)
    ).scalar_one_or_none()
    if not strat_cfg:
        strat_cfg = StrategyConfig(
            name="risk_aware_etf_rotation_v1", version="v1",
            parameters={"max_holdings": 5, "max_concentration": 0.30,
                       "min_positions": 3, "max_turnover": 0.50},
        )
        db.add(strat_cfg)
        db.flush()

    config = BacktestConfig(
        strategy_config_id=strat_cfg.id,
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
    db.commit()
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
    """Compare backtest run vs a second run or benchmark."""
    run = db.execute(select(BacktestRun).where(BacktestRun.id == run_id)).scalar_one_or_none()
    if not run:
        return {"error": "Run not found"}

    # Get strategy A equity
    snaps_a = list(db.execute(
        select(PortfolioSnapshot).where(PortfolioSnapshot.run_id == run_id).order_by(PortfolioSnapshot.date)
    ).scalars().all())
    equity_a = [{"date": str(s.date), "total_value": s.total_value} for s in snaps_a]

    # Get metrics
    metrics = list(db.execute(
        select(PerformanceMetric).where(PerformanceMetric.run_id == run_id)
    ).scalars().all())
    metrics_dict = {m.metric_name: m.value for m in metrics}

    return {
        "run_id": run_id,
        "equity_curve": equity_a,
        "metrics": metrics_dict,
        "note": "For A/B comparison, run two backtests and compare their metrics",
    }


class CompareRequest(BaseModel):
    run_id_a: int
    run_id_b: int


@router.post("/compare")
def compare_runs(req: CompareRequest, db: Session = Depends(get_db)):
    """Compare two backtest runs side by side."""
    run_a = db.execute(select(BacktestRun).where(BacktestRun.id == req.run_id_a)).scalar_one_or_none()
    run_b = db.execute(select(BacktestRun).where(BacktestRun.id == req.run_id_b)).scalar_one_or_none()

    if not run_a or not run_b:
        return {"error": "One or both runs not found"}

    def get_metrics(rid): return {m.metric_name: m.value for m in db.execute(
        select(PerformanceMetric).where(PerformanceMetric.run_id == rid)
    ).scalars().all()}

    m_a = get_metrics(req.run_id_a)
    m_b = get_metrics(req.run_id_b)

    comparison = {}
    for key in set(list(m_a.keys()) + list(m_b.keys())):
        va, vb = m_a.get(key, 0), m_b.get(key, 0)
        comparison[key] = {
            "A": va, "B": vb,
            "delta": va - vb,
            "winner": "A" if va > vb else "B" if vb > va else "tie",
        }

    return {
        "run_id_a": req.run_id_a,
        "run_id_b": req.run_id_b,
        "comparison": comparison,
        "summary": {
            "a_wins": sum(1 for v in comparison.values() if v["winner"] == "A"),
            "b_wins": sum(1 for v in comparison.values() if v["winner"] == "B"),
            "ties": sum(1 for v in comparison.values() if v["winner"] == "tie"),
        },
    }
