from datetime import date as date_type
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
