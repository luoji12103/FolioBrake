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

VALID_TIMEFRAMES = ("daily", "weekly", "monthly")


class FeatureRegistry:
    def __init__(self, db: Session):
        self.db = db

    def register(self, definition: FeatureDefinition) -> FeatureDefinition:
        existing = self.db.execute(
            select(FeatureDefinition)
            .where(FeatureDefinition.name == definition.name)
            .where(FeatureDefinition.timeframe == definition.timeframe)
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
            [{"name": d.name, "lookback_days": d.lookback_days, "parameters": d.parameters, "timeframe": d.timeframe}
             for d in sorted(definitions, key=lambda x: x.name)],
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def _get_daily_bars(self, instrument_id: int, as_of_date: date) -> list[DailyBar]:
        return list(self.db.execute(
            select(DailyBar)
            .where(DailyBar.instrument_id == instrument_id, DailyBar.trade_date <= as_of_date)
            .order_by(DailyBar.trade_date.asc())
        ).scalars().all())

    def _aggregate_bars(self, daily_bars: list[DailyBar], timeframe: str) -> list[dict]:
        if timeframe == "daily":
            return [
                {"open": b.open, "high": b.high, "low": b.low, "close": b.close,
                 "volume": b.volume, "date": b.trade_date}
                for b in daily_bars
            ]

        buckets: dict[tuple, list[DailyBar]] = {}
        for bar in daily_bars:
            if timeframe == "weekly":
                key = bar.trade_date.isocalendar()[:2]
            else:
                key = (bar.trade_date.year, bar.trade_date.month)
            buckets.setdefault(key, []).append(bar)

        aggregated = []
        for key in sorted(buckets):
            group = buckets[key]
            aggregated.append({
                "open": group[0].open,
                "high": max(b.high for b in group),
                "low": min(b.low for b in group),
                "close": group[-1].close,
                "volume": sum(b.volume for b in group),
                "date": group[-1].trade_date,
            })
        return aggregated

    def compute_all(self, instrument_id: int, as_of_date: date, timeframe: str = "daily") -> dict[str, float]:
        if timeframe not in VALID_TIMEFRAMES:
            raise ValueError(f"Invalid timeframe '{timeframe}'. Must be one of {VALID_TIMEFRAMES}")

        instrument = self.db.execute(
            select(Instrument).where(Instrument.id == instrument_id)
        ).scalar_one()

        definitions = list(self.db.execute(
            select(FeatureDefinition).where(FeatureDefinition.timeframe == timeframe)
        ).scalars().all())

        if not definitions:
            return {}

        config_hash = self._compute_config_hash(definitions)

        daily_bars = self._get_daily_bars(instrument_id, as_of_date)
        if len(daily_bars) < 2:
            return {}

        bars = self._aggregate_bars(daily_bars, timeframe)

        prices = [b["close"] for b in bars]
        volumes = [b["volume"] for b in bars]
        dates = [b["date"] for b in bars]

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
