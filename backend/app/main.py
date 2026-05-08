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
from app.api.analysis import router as analysis_router
from app.api.ml import router as ml_router
from app.api.nlp import router as nlp_router
from app.api.auth import router as auth_router
from app.api.social import router as social_router
from app.api.config import router as config_router

from app.core.config import settings
from app.core.logging_config import CorrelationIdMiddleware, setup_logging, get_logger
from app.core.metrics import PrometheusMiddleware, get_metrics_response
from app.core.rate_limit import RateLimiter

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
    setup_logging(json_format=settings.LOG_JSON, level=settings.LOG_LEVEL)
    log = get_logger("startup")
    log.info("starting_application", env=settings.APP_ENV)

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
    log.info("application_ready")
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


_openapi_tags = [
    {"name": "data", "description": "ETF data sync and retrieval"},
    {"name": "features", "description": "Feature engineering and factor registry"},
    {"name": "risk", "description": "Risk state machine, alerts, VaR, and overlays"},
    {"name": "strategy", "description": "Strategy rotation and constraints"},
    {"name": "backtest", "description": "Historical backtesting engine"},
    {"name": "audit", "description": "Trade audit and grading"},
    {"name": "paper", "description": "Paper-trading engine"},
    {"name": "analysis", "description": "Technical indicators, stress tests, Monte Carlo"},
    {"name": "reports", "description": "PDF/HTML report generation"},
    {"name": "configuration", "description": "Runtime configuration management with version control"},
    {"name": "monitoring", "description": "Health, metrics, and observability"},
]

app = FastAPI(
    title="Retail ETF Guardian API",
    version="0.2.0",
    description=(
        "Risk-aware ETF rotation, audit, and do-not-trade backend.\n\n"
        "Provides data sync, feature engineering, risk state machine, "
        "backtesting, paper trading, and reporting for A-share ETFs."
    ),
    openapi_tags=_openapi_tags,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(PrometheusMiddleware)

from app.core.response_cache import ResponseCacheMiddleware
app.add_middleware(ResponseCacheMiddleware)

app.include_router(data_router, prefix="/api/data", tags=["data"])
app.include_router(features_router, prefix="/api/features", tags=["features"])
app.include_router(risk_router, prefix="/api/risk", tags=["risk"])
app.include_router(strategy_router, prefix="/api/strategy", tags=["strategy"])
app.include_router(backtest_router, prefix="/api/backtest", tags=["backtest"])
app.include_router(audit_router, prefix="/api/audit", tags=["audit"])
app.include_router(paper_router, prefix="/api/paper", tags=["paper"])
app.include_router(websocket_router, tags=["websocket"])
app.include_router(reports_router, prefix="/api/reports", tags=["reports"])
app.include_router(analysis_router, prefix="/api/analysis", tags=["analysis"])
app.include_router(ml_router, prefix="/api/ml", tags=["ml"])
app.include_router(nlp_router, prefix="/api/nlp", tags=["nlp"])
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(social_router, prefix="/api/social", tags=["social"])
app.include_router(config_router, prefix="/api/config", tags=["configuration"])


@app.get("/api/health", tags=["monitoring"])
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.2.0"}


@app.get("/metrics", tags=["monitoring"], include_in_schema=False)
def metrics():
    return get_metrics_response()


rate_limiter = RateLimiter(
    calls=settings.RATE_LIMIT_CALLS,
    period=settings.RATE_LIMIT_PERIOD,
)


@app.middleware("http")
async def rate_limit_middleware(request, call_next):
    await rate_limiter(request)
    return await call_next(request)
