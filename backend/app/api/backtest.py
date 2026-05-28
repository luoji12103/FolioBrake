from datetime import date as date_type
from typing import Any
import itertools
import concurrent.futures

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.core.auth import verify_api_key
from app.db.base import get_db
from app.strategy.models import StrategyConfig
from app.backtest.models import BacktestConfig, BacktestRun, PortfolioSnapshot, SimulatedTrade, PerformanceMetric
from app.backtest.engine import BacktestEngine

router = APIRouter(tags=["backtest"])


class BacktestConfigRequest(BaseModel):
    strategy_config_id: int = 1
    start_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    initial_capital: float = Field(100000.0, gt=0, le=1_000_000_000)
    benchmark_symbol: str = Field("510050", max_length=20)


@router.post(
    "/run",
    summary="Run backtest",
    description=(
        "Execute a historical backtest with the specified strategy configuration. "
        "Simulates trading over the date range with realistic cost models "
        "(commission: 3bps, slippage: 10bps). Returns run ID for fetching results."
    ),
)
def run_backtest(req: BacktestConfigRequest, db: Session = Depends(get_db), _: str = Depends(verify_api_key)):
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


@router.post("/run-async")
def run_backtest_async(req: BacktestConfigRequest, _: str = Depends(verify_api_key)):
    from app.workers.tasks import run_backtest as run_backtest_task
    task = run_backtest_task.delay(  # type: ignore[attr-defined]
        strategy_config_id=req.strategy_config_id,
        start_date=req.start_date,
        end_date=req.end_date,
        initial_capital=req.initial_capital,
        benchmark_symbol=req.benchmark_symbol,
    )
    return {"task_id": task.id, "status": "queued"}


@router.get("/task-status/{task_id}")
def get_task_status(task_id: str):
    from app.workers.celery_app import celery_app
    result = celery_app.AsyncResult(task_id)
    response = {"task_id": task_id, "status": result.status}
    if result.status == "PROGRESS":
        response["progress"] = result.info
    elif result.ready():
        response["result"] = result.get()
    return response


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

    # Get config
    config = db.execute(select(BacktestConfig).where(BacktestConfig.id == run.config_id)).scalar_one_or_none()
    strat_cfg = None
    if config:
        strat_cfg = db.execute(select(StrategyConfig).where(StrategyConfig.id == config.strategy_config_id)).scalar_one_or_none()

    snapshots = list(db.execute(
        select(PortfolioSnapshot).where(PortfolioSnapshot.run_id == run_id).order_by(PortfolioSnapshot.date)
    ).scalars().all())
    equity_curve = [{"date": str(s.date), "value": s.total_value} for s in snapshots]

    metrics = list(db.execute(
        select(PerformanceMetric).where(PerformanceMetric.run_id == run_id)
    ).scalars().all())
    metrics_dict = {m.metric_name: m.value for m in metrics}

    trades = list(db.execute(
        select(SimulatedTrade).where(SimulatedTrade.run_id == run_id).order_by(SimulatedTrade.date)
    ).scalars().all())
    trade_log = [{"date": str(t.date), "symbol": str(t.instrument_id), "action": t.side,
                  "quantity": t.quantity, "price": t.price, "notional": t.quantity * t.price,
                  "reason": "strategy signal"} for t in trades]

    return {
        "run_id": str(run.id),
        "config": {
            "strategy": strat_cfg.name if strat_cfg else "unknown",
            "start_date": str(config.start_date) if config else "",
            "end_date": str(config.end_date) if config else "",
            "initial_capital": config.initial_capital if config else 0,
            "benchmark": config.benchmark_symbol if config else "",
        },
        "metrics": metrics_dict,
        "trade_log": trade_log,
        "benchmark_comparison": [],
        "equity_curve": equity_curve,
    }


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


class OptimizationRequest(BaseModel):
    start_date: str
    end_date: str
    initial_capital: float = 100000.0
    benchmark_symbol: str = "510050"
    param_grid: dict[str, list[Any]] = Field(
        ...,
        description='Parameter grid, e.g. {"max_holdings": [3, 5, 7], "max_concentration": [0.2, 0.3, 0.4]}',
    )
    metric: str = Field(
        default="sharpe_ratio",
        description="Metric to optimise: sharpe_ratio, cagr, total_return, max_drawdown, volatility",
    )


def _run_single_backtest(
    strategy_params: dict,
    start_date: str,
    end_date: str,
    initial_capital: float,
    benchmark_symbol: str,
) -> dict:
    """Isolated DB session for thread-pool safety."""
    from app.db.base import SessionLocal

    db = SessionLocal()
    try:
        config = StrategyConfig(
            name="optimization",
            version="v1",
            parameters=strategy_params,
        )
        db.add(config)
        db.flush()

        bt_config = BacktestConfig(
            strategy_config_id=config.id,
            start_date=date_type.fromisoformat(start_date),
            end_date=date_type.fromisoformat(end_date),
            initial_capital=initial_capital,
            cost_model={"commission": 0.0003, "slippage": 0.001},
            benchmark_symbol=benchmark_symbol,
        )
        db.add(bt_config)
        db.flush()

        engine = BacktestEngine(db)
        run = engine.run(bt_config)
        db.commit()

        metrics = {
            m.metric_name: m.value
            for m in db.execute(
                select(PerformanceMetric).where(PerformanceMetric.run_id == run.id)
            ).scalars().all()
        }
        return {"params": strategy_params, "run_id": run.id, "metrics": metrics}
    except Exception as exc:
        db.rollback()
        return {"params": strategy_params, "run_id": None, "metrics": {}, "error": str(exc)}
    finally:
        db.close()


@router.post("/optimize")
def run_optimization(req: OptimizationRequest, db: Session = Depends(get_db)):
    param_names = list(req.param_grid.keys())
    param_values = list(req.param_grid.values())
    combinations = list(itertools.product(*param_values))

    if len(combinations) > 500:
        return {"error": f"Grid too large ({len(combinations)} combinations). Max 500."}

    strategy_params_list = [dict(zip(param_names, combo)) for combo in combinations]

    results: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, len(strategy_params_list))) as pool:
        futures = {
            pool.submit(
                _run_single_backtest,
                params,
                req.start_date,
                req.end_date,
                req.initial_capital,
                req.benchmark_symbol,
            ): params
            for params in strategy_params_list
        }
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    successful = [r for r in results if r.get("run_id") is not None]
    errors = [r for r in results if r.get("error")]

    if not successful:
        return {"error": "All backtest runs failed", "details": errors}

    # Rank by chosen metric (higher is better; negate drawdown/volatility)
    lower_is_better = {"max_drawdown", "volatility"}

    def sort_key(r):
        val = r["metrics"].get(req.metric, 0)
        return -val if req.metric in lower_is_better else val

    successful.sort(key=sort_key, reverse=True)
    best = successful[0]

    return {
        "total_combinations": len(combinations),
        "successful_runs": len(successful),
        "failed_runs": len(errors),
        "optimization_metric": req.metric,
        "best_params": best["params"],
        "best_run_id": best["run_id"],
        "best_metrics": best["metrics"],
        "all_results": [
            {"params": r["params"], "run_id": r["run_id"], "metrics": r["metrics"]}
            for r in successful
        ],
    }
