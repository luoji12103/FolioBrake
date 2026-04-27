"""Seed default feature definitions into the database."""
from app.features.models import FeatureDefinition
from app.db.base import SessionLocal

FEATURES = [
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

db = SessionLocal()
for name, cat, lookback, params in FEATURES:
    existing = db.query(FeatureDefinition).filter(FeatureDefinition.name == name).first()
    if not existing:
        db.add(FeatureDefinition(name=name, category=cat, lookback_days=lookback, parameters=params))
db.commit()
db.close()
print(f"Seeded {len(FEATURES)} feature definitions")
