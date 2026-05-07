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
        "run_id": str(audit.id),
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
        "run_id": str(audit.id),
        "grade": audit.grade,
        "score": audit.score,
        "max_score": 100,
        "summary": audit.summary,
        "created_at": str(audit.created_at) if hasattr(audit, 'created_at') and audit.created_at else "",
        "checks": [{
            "id": str(c.id),
            "category": c.check_name.split("_")[0] if "_" in c.check_name else "general",
            "name": c.check_name,
            "description": c.detail or "",
            "result": "PASS" if c.status == "PASS" else ("WARN" if c.status == "WARN" else "FAIL"),
            "detail": c.detail or "",
        } for c in checks],
    }


@router.get("/report/{run_id}")
def get_audit_report(run_id: int, db: Session = Depends(get_db)):
    return get_audit_status(run_id, db)
