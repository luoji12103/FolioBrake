from collections import defaultdict
from datetime import date as date_type

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.db.base import get_db
from app.paper.models import PaperPortfolio, PaperPosition, PaperOrder, PaperLedger
from app.paper.engine import PaperTradingEngine
from app.data.models import DailyBar

router = APIRouter(tags=["paper"])


class CreatePortfolioRequest(BaseModel):
    name: str = "default"
    initial_capital: float = 100000.0


class ApplySignalRequest(BaseModel):
    portfolio_id: int
    signal_date: str
    target_weights: dict[str, float]  # {"instrument_id": weight, ...}


@router.post("/portfolio")
def create_portfolio(req: CreatePortfolioRequest, db: Session = Depends(get_db)):
    engine = PaperTradingEngine(db)
    pf = engine.create_portfolio(req.name, req.initial_capital)
    db.commit()
    return {"portfolio_id": pf.id, "name": pf.name, "initial_capital": pf.initial_capital}


@router.get("/portfolios")
def list_portfolios(db: Session = Depends(get_db)):
    """List all paper portfolios."""
    portfolios = list(db.execute(
        select(PaperPortfolio).order_by(PaperPortfolio.id)
    ).scalars().all())
    return [{"id": p.id, "name": p.name, "initial_capital": p.initial_capital, "created_at": str(p.created_at)} for p in portfolios]


@router.get("/portfolios/{portfolio_id}")
def get_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    """Get a single paper portfolio."""
    pf = db.execute(select(PaperPortfolio).where(PaperPortfolio.id == portfolio_id)).scalar_one_or_none()
    if not pf:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    from app.paper.engine import PaperTradingEngine
    engine = PaperTradingEngine(db)
    pnl = engine.get_pnl(portfolio_id)
    return {"id": pf.id, "name": pf.name, "initial_capital": pf.initial_capital, "pnl": pnl, "created_at": str(pf.created_at)}


@router.put("/portfolios/{portfolio_id}")
def rename_portfolio(portfolio_id: int, name: str = Query(...), db: Session = Depends(get_db)):
    """Rename a paper portfolio."""
    pf = db.execute(select(PaperPortfolio).where(PaperPortfolio.id == portfolio_id)).scalar_one_or_none()
    if not pf:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    pf.name = name
    db.commit()
    return {"portfolio_id": pf.id, "name": pf.name}


class PreviewRequest(BaseModel):
    portfolio_id: int
    signal_date: str
    target_weights: dict[str, float]


@router.post("/preview-rebalance")
def preview_rebalance(req: PreviewRequest, db: Session = Depends(get_db)):
    """Preview rebalance: show what WOULD happen without executing.

    Returns current positions, target positions, trades needed, and cost estimates.
    """
    engine = PaperTradingEngine(db)
    pf = db.execute(select(PaperPortfolio).where(PaperPortfolio.id == req.portfolio_id)).scalar_one_or_none()
    if not pf:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    total_value = engine.get_pnl(req.portfolio_id)["total_value"]
    weights = {int(k): float(v) for k, v in req.target_weights.items()}

    # Current positions
    current = list(db.execute(
        select(PaperPosition).where(PaperPosition.portfolio_id == req.portfolio_id)
    ).scalars().all())

    trades = []
    estimated_cost = 0.0
    COMM = 0.0003  # commission
    SLIP = 0.001   # slippage

    current_map = {p.instrument_id: p for p in current}

    for inst_id, target_w in weights.items():
        target_value = total_value * target_w
        bar = db.execute(
            select(DailyBar).where(DailyBar.instrument_id == inst_id)
            .order_by(desc(DailyBar.trade_date)).limit(1)
        ).scalar_one_or_none()
        if not bar:
            continue

        existing = current_map.get(inst_id)
        current_value = existing.quantity * bar.close if existing else 0.0
        delta_value = target_value - current_value

        if abs(delta_value) > 1.0:
            side = "BUY" if delta_value > 0 else "SELL"
            trade_cost = abs(delta_value) * (COMM + SLIP)
            estimated_cost += trade_cost
            trades.append({
                "symbol": str(inst_id),
                "side": side,
                "current_value": round(current_value, 2),
                "target_value": round(target_value, 2),
                "delta": round(delta_value, 2),
                "estimated_cost": round(trade_cost, 2),
            })

    return {
        "portfolio_id": req.portfolio_id,
        "total_value": round(total_value, 2),
        "estimated_total_cost": round(estimated_cost, 2),
        "cost_pct_of_value": round(estimated_cost / total_value * 100, 4) if total_value > 0 else 0,
        "trades": trades,
        "trade_count": len(trades),
    }


@router.post("/apply-signal")
def apply_signal(req: ApplySignalRequest, db: Session = Depends(get_db)):
    # Gatekeeper: check latest audit grade
    from app.audit.models import AuditRun
    from sqlalchemy import desc

    latest_audit = db.execute(
        select(AuditRun).order_by(desc(AuditRun.id)).limit(1)
    ).scalar_one_or_none()

    if latest_audit and latest_audit.grade != "GREEN":
        raise HTTPException(
            status_code=403,
            detail=f"Audit gatekeeper blocked: latest audit grade is {latest_audit.grade}. "
                   f"Run audit and achieve GREEN to enable paper trading.",
        )

    engine = PaperTradingEngine(db)
    weights = {int(k): float(v) for k, v in req.target_weights.items()}
    orders = engine.apply_signal(req.portfolio_id, date_type.fromisoformat(req.signal_date), weights)
    db.commit()
    return {"applied": len(orders), "orders": [{"instrument_id": o.instrument_id, "side": o.side,
            "quantity": o.quantity, "price": o.price} for o in orders]}


@router.get("/holdings/{portfolio_id}")
def get_holdings(portfolio_id: int, db: Session = Depends(get_db)):
    positions = list(db.execute(
        select(PaperPosition).where(PaperPosition.portfolio_id == portfolio_id)
    ).scalars().all())
    result = []
    for pos in positions:
        bar = db.execute(
            select(DailyBar)
            .where(DailyBar.instrument_id == pos.instrument_id)
            .order_by(desc(DailyBar.trade_date)).limit(1)
        ).scalar_one_or_none()
        current_price = bar.close if bar else pos.avg_cost
        result.append({
            "instrument_id": pos.instrument_id,
            "quantity": pos.quantity,
            "avg_cost": pos.avg_cost,
            "current_price": current_price,
            "market_value": pos.quantity * current_price,
            "pnl": pos.quantity * (current_price - pos.avg_cost),
        })
    return result


@router.get("/pnl/{portfolio_id}")
def get_pnl(portfolio_id: int, db: Session = Depends(get_db)):
    engine = PaperTradingEngine(db)
    pnl = engine.get_pnl(portfolio_id)
    return {
        "portfolio_id": str(portfolio_id),
        "total_value": pnl.get("total_value", 0),
        "cash": pnl.get("cash", 0),
        "invested": pnl.get("invested", 0),
        "total_pnl": pnl.get("total_pnl", 0),
        "total_pnl_pct": pnl.get("total_pnl_pct", 0),
        "date": date_type.today().isoformat(),
    }


@router.get("/ledger/{portfolio_id}")
def get_ledger(portfolio_id: int, db: Session = Depends(get_db)):
    entries = list(db.execute(
        select(PaperLedger).where(PaperLedger.portfolio_id == portfolio_id).order_by(PaperLedger.date)
    ).scalars().all())
    return [{"date": str(e.date), "entry_type": e.entry_type, "amount": e.amount, "description": e.description}
            for e in entries]


@router.get("/performance/{portfolio_id}")
def get_performance(portfolio_id: int, start_date: str = Query(None), end_date: str = Query(None), db: Session = Depends(get_db)):
    """Compute historical portfolio performance: equity curve, benchmark, drawdown, metrics, monthly returns."""
    pf = db.execute(select(PaperPortfolio).where(PaperPortfolio.id == portfolio_id)).scalar_one_or_none()
    if not pf:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    entries = list(db.execute(
        select(PaperLedger).where(PaperLedger.portfolio_id == portfolio_id).order_by(PaperLedger.date)
    ).scalars().all())
    if not entries:
        return {"portfolio_id": portfolio_id, "equity_curve": [], "benchmark_curve": [],
                "drawdown_curve": [], "metrics": {}, "monthly_returns": []}

    orders = list(db.execute(
        select(PaperOrder).where(PaperOrder.portfolio_id == portfolio_id).order_by(PaperOrder.date)
    ).scalars().all())

    instrument_ids = list(set(o.instrument_id for o in orders))
    benchmark_id = 1
    all_instrument_ids = list(set(instrument_ids + [benchmark_id]))

    bars_by_inst: dict[int, dict] = defaultdict(dict)
    all_bars = list(db.execute(
        select(DailyBar).where(DailyBar.instrument_id.in_(all_instrument_ids)).order_by(DailyBar.trade_date)
    ).scalars().all())
    for bar in all_bars:
        bars_by_inst[bar.instrument_id][bar.trade_date] = bar.close

    all_dates = sorted(set(d for inst_bars in bars_by_inst.values() for d in inst_bars))
    first_date = entries[0].date
    if start_date:
        all_dates = [d for d in all_dates if d >= date_type.fromisoformat(start_date)]
    else:
        all_dates = [d for d in all_dates if d >= first_date]
    if end_date:
        all_dates = [d for d in all_dates if d <= date_type.fromisoformat(end_date)]

    if not all_dates:
        return {"portfolio_id": portfolio_id, "equity_curve": [], "benchmark_curve": [],
                "drawdown_curve": [], "metrics": {}, "monthly_returns": []}

    cash_by_date: dict = {}
    running_cash = 0.0
    entry_idx = 0
    for d in all_dates:
        while entry_idx < len(entries) and entries[entry_idx].date <= d:
            running_cash += entries[entry_idx].amount
            entry_idx += 1
        cash_by_date[d] = running_cash

    position_qty: dict[int, float] = defaultdict(float)
    order_idx = 0
    positions_by_date: dict = {}
    for d in all_dates:
        while order_idx < len(orders) and orders[order_idx].date <= d:
            o = orders[order_idx]
            if o.side == "BUY":
                position_qty[o.instrument_id] += o.quantity
            else:
                position_qty[o.instrument_id] -= o.quantity
            order_idx += 1
        positions_by_date[d] = dict(position_qty)

    equity_curve = []
    for d in all_dates:
        cash = cash_by_date[d]
        holdings = sum(
            positions_by_date[d].get(inst_id, 0) * bars_by_inst[inst_id].get(d, 0)
            for inst_id in instrument_ids
        )
        equity_curve.append({"date": d.isoformat(), "equity": round(cash + holdings, 2)})

    start_equity = equity_curve[0]["equity"]
    benchmark_curve = []
    if benchmark_id in bars_by_inst:
        bench_prices = [bars_by_inst[benchmark_id].get(d) for d in all_dates]
        first_bench = next((p for p in bench_prices if p is not None), None)
        if first_bench and first_bench > 0:
            for d, p in zip(all_dates, bench_prices):
                if p is not None:
                    benchmark_curve.append({
                        "date": d.isoformat(),
                        "value": round(start_equity * (p / first_bench), 2),
                    })

    drawdown_curve = []
    peak = 0.0
    for point in equity_curve:
        eq = point["equity"]
        peak = max(peak, eq)
        dd = ((eq - peak) / peak * 100) if peak > 0 else 0.0
        drawdown_curve.append({"date": point["date"], "drawdown": round(dd, 4)})

    eq_values = np.array([p["equity"] for p in equity_curve])
    metrics = {}
    if len(eq_values) > 1:
        daily_returns = np.diff(eq_values) / eq_values[:-1]
        n_days = (all_dates[-1] - all_dates[0]).days
        n_years = max(n_days / 365.25, 0.01)
        running_max = np.maximum.accumulate(eq_values)
        dd_series = (eq_values - running_max) / running_max

        metrics = {
            "total_return": round(float((eq_values[-1] / eq_values[0] - 1) * 100), 2),
            "cagr": round(float(((eq_values[-1] / eq_values[0]) ** (1 / n_years) - 1) * 100) if eq_values[0] > 0 else 0, 2),
            "sharpe_ratio": round(float(np.mean(daily_returns) / np.std(daily_returns) * np.sqrt(252)) if np.std(daily_returns) > 0 else 0, 4),
            "max_drawdown": round(float(np.min(dd_series) * 100), 2),
            "volatility": round(float(np.std(daily_returns) * np.sqrt(252) * 100), 2),
            "win_rate": round(float(np.sum(daily_returns > 0) / len(daily_returns) * 100), 2),
        }

    monthly_returns = []
    monthly_buckets: dict[str, list[float]] = defaultdict(list)
    for point in equity_curve:
        monthly_buckets[point["date"][:7]].append(point["equity"])
    prev_end = None
    for month in sorted(monthly_buckets):
        month_end = monthly_buckets[month][-1]
        if prev_end is not None and prev_end > 0:
            monthly_returns.append({"month": month, "return": round((month_end / prev_end - 1) * 100, 2)})
        prev_end = month_end

    return {
        "portfolio_id": portfolio_id,
        "equity_curve": equity_curve,
        "benchmark_curve": benchmark_curve,
        "drawdown_curve": drawdown_curve,
        "metrics": metrics,
        "monthly_returns": monthly_returns,
    }
