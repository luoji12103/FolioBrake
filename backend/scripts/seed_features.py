"""Seed default feature definitions into the database."""
from sqlalchemy import select

# Import data models first so Instrument is registered before FeatureValue resolves it
import app.data.models  # noqa: F401
from app.features.models import FeatureDefinition
from app.db.base import SessionLocal

FEATURES = [
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

db = SessionLocal()
count = 0
for name, cat, lookback, params, tf in FEATURES:
    existing = db.execute(select(FeatureDefinition).where(FeatureDefinition.name == name)).scalar_one_or_none()
    if not existing:
        db.add(FeatureDefinition(name=name, category=cat, lookback_days=lookback, parameters=params, timeframe=tf))
        count += 1
db.commit()
db.close()
print(f"Seeded {count} new feature definitions (total {len(FEATURES)})")
