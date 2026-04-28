import hashlib
import json
from datetime import date
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.features.models import FeatureDefinition, FeatureValue, FeatureRun
from app.data.models import DailyBar, Instrument
from app.features.trend import compute_trend_features
from app.features.momentum import compute_momentum_features
from app.features.volatility import compute_volatility_features
from app.features.drawdown import compute_drawdown_features
from app.features.liquidity import compute_liquidity_features


class FeatureRegistry:
    def __init__(self, db: Session):
        self.db = db

    def register(self, definition: FeatureDefinition) -> FeatureDefinition:
        existing = self.db.execute(
            select(FeatureDefinition).where(FeatureDefinition.name == definition.name)
        ).scalar_one_or_none()
        if existing:
            existing.category = definition.category
            existing.lookback_days = definition.lookback_days
            existing.parameters = definition.parameters
            self.db.flush()
            return existing
        self.db.add(definition)
        self.db.flush()
        return definition

    def _compute_config_hash(self, definitions: list[FeatureDefinition]) -> str:
        payload = json.dumps(
            [{"name": d.name, "lookback_days": d.lookback_days, "parameters": d.parameters}
             for d in sorted(definitions, key=lambda x: x.name)],
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def compute_all(self, instrument_id: int, as_of_date: date) -> dict[str, float]:
        instrument = self.db.execute(
            select(Instrument).where(Instrument.id == instrument_id)
        ).scalar_one()
        definitions = list(self.db.execute(select(FeatureDefinition)).scalars().all())
        config_hash = self._compute_config_hash(definitions)

        bars = list(self.db.execute(
            select(DailyBar)
            .where(DailyBar.instrument_id == instrument_id, DailyBar.trade_date <= as_of_date)
            .order_by(DailyBar.trade_date.asc())
        ).scalars().all())

        if len(bars) < 2:
            return {}

        prices = [b.close for b in bars]
        volumes = [b.volume for b in bars]
        dates = [b.trade_date for b in bars]

        all_features: dict[str, float] = {}
        for d in definitions:
            if d.category == "trend":
                all_features.update(compute_trend_features(d.name, prices, dates, d.parameters))
            elif d.category == "momentum":
                all_features.update(compute_momentum_features(d.name, prices, dates, d.parameters))
            elif d.category == "volatility":
                all_features.update(compute_volatility_features(d.name, prices, dates, d.parameters))
            elif d.category == "drawdown":
                all_features.update(compute_drawdown_features(d.name, prices, dates, d.parameters))
            elif d.category == "liquidity":
                all_features.update(compute_liquidity_features(d.name, volumes, dates, d.parameters))

        for d in definitions:
            stmt = pg_insert(FeatureValue).values(
                instrument_id=instrument_id,
                feature_definition_id=d.id,
                date=as_of_date,
                value=all_features.get(d.name, 0.0),
                config_hash=config_hash,
            ).on_conflict_do_update(
                index_elements=["instrument_id", "feature_definition_id", "date", "config_hash"],
                set_={"value": all_features.get(d.name, 0.0)},
            )
            self.db.execute(stmt)

        run = FeatureRun(
            config_hash=config_hash,
            instrument_id=instrument_id,
            as_of_date=as_of_date,
        )
        self.db.add(run)
        self.db.flush()

        return all_features
