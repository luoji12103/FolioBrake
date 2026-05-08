from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.base import get_db
from app.backtest.models import BacktestRun, PerformanceMetric, PortfolioSnapshot, SimulatedTrade
from app.paper.models import PaperPortfolio, PaperPosition, PaperLedger
from app.data.models import DailyBar
import csv
import io
from datetime import datetime

router = APIRouter(tags=["reports"])


@router.get("/backtest/{run_id}/pdf")
def export_backtest_pdf(run_id: int, db: Session = Depends(get_db)):
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
def export_portfolio_csv(portfolio_id: int, db: Session = Depends(get_db)):
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
