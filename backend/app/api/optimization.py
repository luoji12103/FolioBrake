from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["optimization"])

class OptimizationRequest(BaseModel):
    symbols: list[str]
    target_return: float = 0.1
    risk_free_rate: float = 0.03

@router.post("/optimize")
def optimize_portfolio(req: OptimizationRequest):
    n = len(req.symbols)
    equal_weight = 1.0 / n if n > 0 else 0
    return {
        "weights": {s: equal_weight for s in req.symbols},
        "expected_return": req.target_return,
        "method": "equal_weight"
    }
