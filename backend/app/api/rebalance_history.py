from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.base import get_db

router = APIRouter(tags=["rebalance"])

@router.get("/rebalance-history/{portfolio_id}")
def get_rebalance_history(portfolio_id: int, db: Session = Depends(get_db)):
    return {"portfolio_id": portfolio_id, "rebalances": []}
