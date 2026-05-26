from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.base import get_db

router = APIRouter(tags=["portfolio-risk"])

@router.get("/risk-metrics/{portfolio_id}")
def get_risk_metrics(portfolio_id: int, db: Session = Depends(get_db)):
    return {
        "portfolio_id": portfolio_id,
        "var_95": 0.0,
        "cvar_95": 0.0,
        "sharpe_ratio": 0.0,
        "max_drawdown": 0.0,
        "volatility": 0.0,
    }
