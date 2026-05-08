from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, desc, func

from app.db.base import get_db
from app.risk.models import RiskStateRecord, RiskRuleResultRecord, RiskOverlayDecisionRecord, RiskAlert
from app.data.models import Instrument
from app.risk.correlation import CorrelationMonitor
from app.risk.var import compute_tail_metrics

router = APIRouter(tags=["risk"])


@router.get("/state")
def get_risk_state(db: Session = Depends(get_db)):
    state = db.execute(
        select(RiskStateRecord).order_by(desc(RiskStateRecord.date)).limit(1)
    ).scalar_one_or_none()
    if not state:
        return {"state": "NORMAL", "transition_reason": "default"}
    return {"date": str(state.date), "state": state.state, "transition_reason": state.transition_reason}


@router.get("/state-history")
def get_state_history(db: Session = Depends(get_db)):
    """Return last 50 risk state transitions for timeline visualization."""
    states = list(db.execute(
        select(RiskStateRecord).order_by(RiskStateRecord.date.desc()).limit(50)
    ).scalars().all())
    STATE_MAP = {"NORMAL": 0, "CAUTION": 1, "DEFENSIVE": 2, "HALT": 3}
    return [
        {"date": str(s.date), "state": s.state, "state_code": STATE_MAP.get(s.state, 0), "reason": s.transition_reason}
        for s in reversed(states)
    ]


@router.get("/alerts")
def get_alerts(limit: int = Query(20), db: Session = Depends(get_db)):
    alerts = list(db.execute(
        select(RiskAlert).order_by(RiskAlert.timestamp.desc()).limit(limit)
    ).scalars().all())
    unread = db.execute(
        select(func.count()).where(RiskAlert.read == False)
    ).scalar()
    return {
        "alerts": [
            {
                "id": a.id,
                "timestamp": str(a.timestamp),
                "type": a.alert_type,
                "severity": a.severity,
                "title": a.title,
                "message": a.message,
                "read": a.read,
            }
            for a in alerts
        ],
        "unread_count": unread or 0,
    }


@router.get("/rules")
def get_rules(date: str = Query(None), db: Session = Depends(get_db)):
    q = select(RiskRuleResultRecord)
    if date:
        q = q.where(RiskRuleResultRecord.date == date)
    else:
        q = q.order_by(desc(RiskRuleResultRecord.date)).limit(50)
    results = list(db.execute(q).scalars().all())
    return [
        {"date": str(r.date), "rule_name": r.rule_name, "triggered": r.triggered,
         "severity": r.severity, "detail": r.detail}
        for r in results
    ]


@router.get("/overlay")
def get_overlay(db: Session = Depends(get_db)):
    decision = db.execute(
        select(RiskOverlayDecisionRecord).order_by(desc(RiskOverlayDecisionRecord.date)).limit(1)
    ).scalar_one_or_none()
    if not decision:
        return {"decision": "ALLOW", "reason": "No overlay decision yet"}
    return {
        "date": str(decision.date),
        "decision": decision.decision,
        "reason": decision.reason,
        "original_targets": decision.original_targets,
        "final_targets": decision.final_targets,
        "suppressed_trades": decision.suppressed_trades,
    }


@router.get("/correlation")
def get_correlation(lookback: int = Query(default=60), db: Session = Depends(get_db)):
    """Compute pairwise correlations for all universe ETFs."""
    instruments = list(db.execute(select(Instrument)).scalars().all())
    if len(instruments) < 2:
        return {"matrix": [], "warnings": [], "note": "Need at least 2 instruments"}

    from datetime import date as dt
    monitor = CorrelationMonitor(db)
    return monitor.compute_matrix([i.id for i in instruments], dt.today(), lookback)


@router.get("/var")
def get_var_metrics(backtest_run_id: int = Query(default=None), db: Session = Depends(get_db)):
    """Compute VaR and tail risk metrics. If backtest_run_id provided, uses its equity curve."""
    from app.backtest.models import PortfolioSnapshot

    if backtest_run_id:
        snaps = list(db.execute(
            select(PortfolioSnapshot).where(PortfolioSnapshot.run_id == backtest_run_id).order_by(PortfolioSnapshot.date)
        ).scalars().all())
        if snaps:
            equity = [s.total_value for s in snaps]
            metrics = compute_tail_metrics(equity)
            metrics["data_points"] = len(equity)
            return metrics

    return {"note": "Provide backtest_run_id to compute VaR from backtest equity curve"}
