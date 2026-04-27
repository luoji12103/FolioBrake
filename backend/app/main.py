from fastapi import FastAPI

from app.api.data import router as data_router
from app.api.features import router as features_router
from app.api.risk import router as risk_router
from app.api.strategy import router as strategy_router
from app.api.backtest import router as backtest_router
from app.api.audit import router as audit_router
from app.api.paper import router as paper_router

app = FastAPI(title="Retail ETF Guardian API", version="0.1.0")

app.include_router(data_router, prefix="/data", tags=["data"])
app.include_router(features_router, prefix="/features", tags=["features"])
app.include_router(risk_router, prefix="/risk", tags=["risk"])
app.include_router(strategy_router, prefix="/strategy", tags=["strategy"])
app.include_router(backtest_router, prefix="/backtest", tags=["backtest"])
app.include_router(audit_router, prefix="/audit", tags=["audit"])
app.include_router(paper_router, prefix="/paper", tags=["paper"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}
