from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.auth import verify_api_key
from app.db.base import get_db
from app.backtest.models import BacktestRun, PerformanceMetric, PortfolioSnapshot, SimulatedTrade
from app.backtest.models import BacktestConfig
from app.paper.models import PaperPortfolio, PaperPosition, PaperOrder
from app.risk.models import RiskStateRecord, RiskRuleResultRecord
from app.data.models import DailyBar
import csv
import io
from datetime import datetime

router = APIRouter(tags=["reports"])


@router.get("/backtest/{run_id}/pdf")
def export_backtest_pdf(run_id: int, db: Session = Depends(get_db), _: str = Depends(verify_api_key)):
    """Export backtest results as a simple text report (PDF requires reportlab)."""
    run = db.execute(select(BacktestRun).where(BacktestRun.id == run_id)).scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    metrics = list(db.execute(
        select(PerformanceMetric).where(PerformanceMetric.run_id == run_id)
    ).scalars().all())
    metrics_dict = {m.metric_name: m.value for m in metrics}
    
    report = f"""Backtest Report - Run #{run_id}
================================
Status: {run.status}
Generated: {datetime.now().isoformat()}

Performance Metrics:
"""
    for name, value in metrics_dict.items():
        report += f"  {name}: {value:.4f}\n"
    
    return StreamingResponse(
        io.BytesIO(report.encode()),
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=backtest_{run_id}.txt"}
    )


@router.get("/portfolio/{portfolio_id}/csv")
def export_portfolio_csv(portfolio_id: int, db: Session = Depends(get_db), _: str = Depends(verify_api_key)):
    """Export portfolio data as CSV."""
    pf = db.execute(select(PaperPortfolio).where(PaperPortfolio.id == portfolio_id)).scalar_one_or_none()
    if not pf:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    positions = list(db.execute(
        select(PaperPosition).where(PaperPosition.portfolio_id == portfolio_id)
    ).scalars().all())
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Instrument ID", "Quantity", "Avg Cost"])
    for pos in positions:
        writer.writerow([pos.instrument_id, pos.quantity, pos.avg_cost])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=portfolio_{portfolio_id}.csv"}
    )


@router.get("/backtest/{run_id}/pdf-full")
def export_backtest_pdf_full(run_id: int, db: Session = Depends(get_db), _: str = Depends(verify_api_key)):
    from app.reports.generator import ReportGenerator

    run = db.execute(select(BacktestRun).where(BacktestRun.id == run_id)).scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    config = db.execute(
        select(BacktestConfig).where(BacktestConfig.id == run.config_id)
    ).scalar_one_or_none()

    metrics = list(db.execute(
        select(PerformanceMetric).where(PerformanceMetric.run_id == run_id)
    ).scalars().all())
    metrics_dict = {m.metric_name: m.value for m in metrics}

    trades = list(db.execute(
        select(SimulatedTrade).where(SimulatedTrade.run_id == run_id)
    ).scalars().all())

    data = {
        "config": {
            "run_id": run_id,
            "status": run.status,
            "start_date": str(config.start_date) if config else "",
            "end_date": str(config.end_date) if config else "",
            "initial_capital": config.initial_capital if config else 0,
        },
        "metrics": metrics_dict,
        "trades": [{"date": str(t.date), "side": t.side, "quantity": t.quantity} for t in trades],
    }

    gen = ReportGenerator()
    pdf_bytes = gen.generate_backtest_report(data)

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=backtest_{run_id}.pdf"},
    )


@router.get("/portfolio/{portfolio_id}/pdf")
def export_portfolio_pdf(portfolio_id: int, db: Session = Depends(get_db), _: str = Depends(verify_api_key)):
    from app.reports.generator import ReportGenerator

    pf = db.execute(select(PaperPortfolio).where(PaperPortfolio.id == portfolio_id)).scalar_one_or_none()
    if not pf:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    positions = list(db.execute(
        select(PaperPosition).where(PaperPosition.portfolio_id == portfolio_id)
    ).scalars().all())

    pos_list = []
    for p in positions:
        instrument = db.execute(
            select(DailyBar.instrument_id).where(DailyBar.instrument_id == p.instrument_id)
            .order_by(DailyBar.trade_date.desc()).limit(1)
        ).scalar_one_or_none()
        pos_list.append({
            "symbol": f"instrument_{p.instrument_id}",
            "quantity": p.quantity,
            "avg_cost": p.avg_cost,
            "current_price": p.avg_cost,
            "pnl": 0.0,
        })

    data = {
        "overview": {
            "name": pf.name,
            "initial_capital": pf.initial_capital,
            "positions_count": len(positions),
        },
        "positions": pos_list,
    }

    gen = ReportGenerator()
    pdf_bytes = gen.generate_portfolio_report(data)

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=portfolio_{portfolio_id}.pdf"},
    )


@router.get("/risk/pdf")
def export_risk_pdf(db: Session = Depends(get_db), _: str = Depends(verify_api_key)):
    from app.reports.generator import ReportGenerator

    latest_state = db.execute(
        select(RiskStateRecord).order_by(RiskStateRecord.date.desc()).limit(1)
    ).scalar_one_or_none()

    triggered = list(db.execute(
        select(RiskRuleResultRecord).where(RiskRuleResultRecord.triggered == True)
        .order_by(RiskRuleResultRecord.date.desc()).limit(10)
    ).scalars().all())

    data = {
        "state": latest_state.state if latest_state else "UNKNOWN",
        "metrics": {
            "latest_date": str(latest_state.date) if latest_state else "N/A",
            "triggered_rules_count": len(triggered),
        },
        "triggered_rules": [r.rule_name for r in triggered],
    }

    gen = ReportGenerator()
    pdf_bytes = gen.generate_risk_report(data)

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=risk_report.pdf"},
    )
