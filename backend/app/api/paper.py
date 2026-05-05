from datetime import date as date_type
from fastapi import APIRouter, Depends, Query
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
    return engine.get_pnl(portfolio_id)


@router.get("/ledger/{portfolio_id}")
def get_ledger(portfolio_id: int, db: Session = Depends(get_db)):
    entries = list(db.execute(
        select(PaperLedger).where(PaperLedger.portfolio_id == portfolio_id).order_by(PaperLedger.date)
    ).scalars().all())
    return [{"date": str(e.date), "entry_type": e.entry_type, "amount": e.amount, "description": e.description}
            for e in entries]
