from fastapi import FastAPI

from app.api.data import router as data_router
from app.api.features import router as features_router
from app.api.risk import router as risk_router
from app.api.strategy import router as strategy_router

app = FastAPI(title="Retail ETF Guardian API", version="0.1.0")

app.include_router(data_router, prefix="/data", tags=["data"])
app.include_router(features_router, prefix="/features", tags=["features"])
app.include_router(risk_router, prefix="/risk", tags=["risk"])
app.include_router(strategy_router, prefix="/strategy", tags=["strategy"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}
