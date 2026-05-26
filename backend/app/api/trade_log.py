from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.base import get_db

router = APIRouter(tags=["trades"])

@router.get("/trade-log/{portfolio_id}")
def get_trade_log(portfolio_id: int, db: Session = Depends(get_db)):
    return {"portfolio_id": portfolio_id, "trades": []}
