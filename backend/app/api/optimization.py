from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.auth import verify_api_key

router = APIRouter(tags=["optimization"])


class OptimizationRequest(BaseModel):
    symbols: list[str] = Field(..., min_length=1, max_length=50)
    target_return: float = Field(0.1, ge=-1.0, le=5.0)
    risk_free_rate: float = Field(0.03, ge=0.0, le=0.5)


@router.post("/optimize")
def optimize_portfolio(req: OptimizationRequest, _: str = Depends(verify_api_key)):
    n = len(req.symbols)
    equal_weight = 1.0 / n if n > 0 else 0
    return {
        "weights": {s: equal_weight for s in req.symbols},
        "expected_return": req.target_return,
        "method": "equal_weight",
    }
