from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.db.base import get_db
from app.risk.models import RiskStateRecord, RiskRuleResultRecord, RiskOverlayDecisionRecord

router = APIRouter(tags=["risk"])


@router.get("/state")
def get_risk_state(db: Session = Depends(get_db)):
    state = db.execute(
        select(RiskStateRecord).order_by(desc(RiskStateRecord.date)).limit(1)
    ).scalar_one_or_none()
    if not state:
        return {"state": "NORMAL", "transition_reason": "default"}
    return {"date": str(state.date), "state": state.state, "transition_reason": state.transition_reason}


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
