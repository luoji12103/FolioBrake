from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.data import router as data_router
from app.api.features import router as features_router
from app.api.risk import router as risk_router
from app.api.strategy import router as strategy_router
from app.api.backtest import router as backtest_router
from app.api.audit import router as audit_router
from app.api.paper import router as paper_router

FEATURE_SEEDS = [
    ("trend_sma_60", "trend", 60, {"window": 60}),
    ("trend_sma_120", "trend", 120, {"window": 120}),
    ("trend_sma_200", "trend", 200, {"window": 200}),
    ("trend_ema_crossover", "trend", 26, {}),
    ("momentum_1m", "momentum", 21, {"window": 21}),
    ("momentum_3m", "momentum", 63, {"window": 63}),
    ("momentum_6m", "momentum", 126, {"window": 126}),
    ("momentum_12m", "momentum", 252, {"window": 252}),
    ("momentum_risk_adj", "momentum", 126, {}),
    ("volatility_20d", "volatility", 20, {"window": 20}),
    ("volatility_60d", "volatility", 60, {"window": 60}),
    ("volatility_percentile", "volatility", 252, {}),
    ("drawdown_60d", "drawdown", 60, {"window": 60}),
    ("drawdown_120d", "drawdown", 120, {"window": 120}),
    ("drawdown_max", "drawdown", 252, {}),
    ("liquidity_adv_20d", "liquidity", 20, {"window": 20}),
    ("liquidity_volume_trend", "liquidity", 60, {}),
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.db.base import SessionLocal
    from app.features.models import FeatureDefinition
    from sqlalchemy import select

    db = SessionLocal()
    try:
        existing = db.execute(select(FeatureDefinition).limit(1)).scalar_one_or_none()
        if not existing:
            for name, cat, lookback, params in FEATURE_SEEDS:
                db.add(FeatureDefinition(name=name, category=cat, lookback_days=lookback, parameters=params))
            db.commit()
    finally:
        db.close()
    yield


app = FastAPI(title="Retail ETF Guardian API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data_router, prefix="/api/data", tags=["data"])
app.include_router(features_router, prefix="/api/features", tags=["features"])
app.include_router(risk_router, prefix="/api/risk", tags=["risk"])
app.include_router(strategy_router, prefix="/api/strategy", tags=["strategy"])
app.include_router(backtest_router, prefix="/api/backtest", tags=["backtest"])
app.include_router(audit_router, prefix="/api/audit", tags=["audit"])
app.include_router(paper_router, prefix="/api/paper", tags=["paper"])


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}
