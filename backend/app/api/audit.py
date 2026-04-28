from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from datetime import date
from app.db.base import get_db
from app.strategy.models import StrategyConfig
from app.backtest.models import BacktestConfig
from app.audit.models import AuditRun, AuditCheckResult
from app.audit.grading import AuditGrader

router = APIRouter(tags=["audit"])


class AuditRequest(BaseModel):
    strategy_config_id: int = 1
    backtest_config_id: int = 1


@router.post("/run")
def run_audit(req: AuditRequest, db: Session = Depends(get_db)):
    # Look up or create strategy config
    strat_cfg = db.execute(
        select(StrategyConfig).where(StrategyConfig.id == req.strategy_config_id)
    ).scalar_one_or_none()
    if not strat_cfg:
        strat_cfg = StrategyConfig(name="risk_aware_etf_rotation_v1", version="v1")
        db.add(strat_cfg)
        db.flush()

    # Look up or create backtest config
    btc = db.execute(
        select(BacktestConfig).where(BacktestConfig.id == req.backtest_config_id)
    ).scalar_one_or_none()
    if not btc:
        btc = BacktestConfig(
            strategy_config_id=strat_cfg.id,
            start_date=date.today().replace(year=date.today().year - 1),
            end_date=date.today(),
            initial_capital=100000.0,
        )
        db.add(btc)
        db.flush()

    grader = AuditGrader(db)
    audit = grader.run_audit(strat_cfg.id, btc.id)
    db.commit()
    return {
        "audit_id": audit.id,
        "grade": audit.grade,
        "score": audit.score,
        "summary": audit.summary,
    }


@router.get("/status/{run_id}")
def get_audit_status(run_id: int, db: Session = Depends(get_db)):
    audit = db.execute(select(AuditRun).where(AuditRun.id == run_id)).scalar_one_or_none()
    if not audit:
        return {"error": "Audit run not found"}
    checks = list(db.execute(select(AuditCheckResult).where(AuditCheckResult.audit_run_id == audit.id)).scalars().all())
    return {
        "audit_id": audit.id,
        "grade": audit.grade,
        "score": audit.score,
        "summary": audit.summary,
        "checks": [{"check_name": c.check_name, "status": c.status, "score": c.score, "detail": c.detail} for c in checks],
    }


@router.get("/report/{run_id}")
def get_audit_report(run_id: int, db: Session = Depends(get_db)):
    return get_audit_status(run_id, db)
