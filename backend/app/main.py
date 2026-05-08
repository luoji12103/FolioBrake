import asyncio
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
from app.api.websocket import router as websocket_router
from app.api.reports import router as reports_router

FEATURE_SEEDS = [
    ("trend_sma_60", "trend", 60, {"window": 60}, "daily"),
    ("trend_sma_120", "trend", 120, {"window": 120}, "daily"),
    ("trend_sma_200", "trend", 200, {"window": 200}, "daily"),
    ("trend_ema_crossover", "trend", 26, {}, "daily"),
    ("momentum_1m", "momentum", 21, {"window": 21}, "daily"),
    ("momentum_3m", "momentum", 63, {"window": 63}, "daily"),
    ("momentum_6m", "momentum", 126, {"window": 126}, "daily"),
    ("momentum_12m", "momentum", 252, {"window": 252}, "daily"),
    ("momentum_risk_adj", "momentum", 126, {}, "daily"),
    ("volatility_20d", "volatility", 20, {"window": 20}, "daily"),
    ("volatility_60d", "volatility", 60, {"window": 60}, "daily"),
    ("volatility_percentile", "volatility", 252, {}, "daily"),
    ("drawdown_60d", "drawdown", 60, {"window": 60}, "daily"),
    ("drawdown_120d", "drawdown", 120, {"window": 120}, "daily"),
    ("drawdown_max", "drawdown", 252, {}, "daily"),
    ("liquidity_adv_20d", "liquidity", 20, {"window": 20}, "daily"),
    ("liquidity_volume_trend", "liquidity", 60, {}, "daily"),
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.db.base import SessionLocal
    from app.features.models import FeatureDefinition
    from app.api.websocket import price_broadcaster
    from sqlalchemy import select

    db = SessionLocal()
    try:
        existing = db.execute(select(FeatureDefinition).limit(1)).scalar_one_or_none()
        if not existing:
            for name, cat, lookback, params, tf in FEATURE_SEEDS:
                db.add(FeatureDefinition(name=name, category=cat, lookback_days=lookback, parameters=params, timeframe=tf))
            db.commit()
    finally:
        db.close()

    task = asyncio.create_task(price_broadcaster())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


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
app.include_router(websocket_router, tags=["websocket"])
app.include_router(reports_router, prefix="/api/reports", tags=["reports"])


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}
