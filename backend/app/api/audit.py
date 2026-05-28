from collections import defaultdict

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from datetime import date
from app.core.auth import verify_api_key
from app.db.base import get_db
from app.strategy.models import StrategyConfig
from app.backtest.models import BacktestConfig
from app.audit.models import AuditRun, AuditCheckResult
from app.audit.grading import AuditGrader, CHECK_WEIGHTS

router = APIRouter(tags=["audit"])


class AuditRequest(BaseModel):
    strategy_config_id: int = 1
    backtest_config_id: int = 1


@router.post("/run")
def run_audit(req: AuditRequest, db: Session = Depends(get_db), _: str = Depends(verify_api_key)):
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


def _get_check_visualization(check: AuditCheckResult) -> dict:
    name = check.check_name
    detail = check.detail if isinstance(check.detail, dict) else {}

    if name == "leakage":
        return {
            "type": "bar",
            "data": {"passed": check.score, "failed": 100 - check.score},
        }
    if name == "walk_forward":
        return {"type": "line", "data": detail.get("folds", [])}
    if name == "param_stability":
        return {"type": "scatter", "data": detail.get("params", [])}
    if name == "cost_stress":
        return {
            "type": "bar",
            "data": {
                "commission": detail.get("commission", 0),
                "slippage": detail.get("slippage", 0),
            },
        }
    if name == "turnover_feasibility":
        return {
            "type": "bar",
            "data": {
                "turnover": detail.get("max_turnover", 0),
                "limit": 1.0,
            },
        }
    return {"type": "gauge", "data": {"value": check.score}}


def _get_grade_history(db: Session) -> list[dict]:
    audits = list(
        db.execute(select(AuditRun).order_by(AuditRun.id.desc()).limit(10))
        .scalars()
        .all()
    )
    return [
        {
            "id": a.id,
            "grade": a.grade,
            "score": a.score,
            "date": str(a.created_at) if a.created_at else str(a.run_date),
        }
        for a in reversed(audits)
    ]


def _get_score_breakdown(checks: list[AuditCheckResult]) -> dict:
    categories: dict[str, dict] = defaultdict(lambda: {"total": 0, "passed": 0, "score": 0.0})
    for c in checks:
        cat = c.check_name.split("_")[0] if "_" in c.check_name else "general"
        categories[cat]["total"] += 1
        if c.status == "PASS":
            categories[cat]["passed"] += 1
        categories[cat]["score"] += c.score
    return dict(categories)


@router.get("/report/{run_id}")
def get_audit_report(run_id: int, db: Session = Depends(get_db)):
    audit = db.execute(
        select(AuditRun).where(AuditRun.id == run_id)
    ).scalar_one_or_none()
    if not audit:
        return {"error": "Audit run not found"}

    checks = list(
        db.execute(
            select(AuditCheckResult).where(AuditCheckResult.audit_run_id == audit.id)
        )
        .scalars()
        .all()
    )

    enhanced_checks = []
    for c in checks:
        enhanced_checks.append(
            {
                "id": c.id,
                "name": c.check_name,
                "category": c.check_name.split("_")[0] if "_" in c.check_name else "general",
                "status": c.status,
                "score": c.score,
                "weight": CHECK_WEIGHTS.get(c.check_name, 0.10),
                "detail": c.detail or "",
                "visualization": _get_check_visualization(c),
            }
        )

    return {
        "run_id": str(audit.id),
        "grade": audit.grade,
        "score": audit.score,
        "max_score": 100,
        "summary": audit.summary,
        "created_at": str(audit.created_at) if audit.created_at else str(audit.run_date),
        "checks": enhanced_checks,
        "grade_history": _get_grade_history(db),
        "score_breakdown": _get_score_breakdown(checks),
    }
