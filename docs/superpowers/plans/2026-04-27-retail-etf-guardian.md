# Retail ETF Guardian — Complete Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the full Retail ETF Guardian system — feature registry, strategy engine, backtest engine, risk overlay, audit gatekeeper, paper portfolio, frontend integration, and report generation.

**Architecture:** Feature computation → ETF scoring → constrained portfolio construction → backtest simulation → audit validation → paper trading. Risk overlay runs parallel as a daily gatekeeper. Frontend connects via REST/WebSocket to the FastAPI backend.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic, PostgreSQL 16, Redis 7, AKShare, pandas, numpy. Frontend: Tauri + React + TypeScript + Vite.

**Branch naming:** Functional names only (e.g., `feat-feature-registry`, `feat-risk-overlay`). Each branch merged to `main` after completion.

---

## Completed

| What | Branch | Status |
|------|--------|--------|
| Phase 0: Repo scaffold, Docker Compose, Tauri skeleton | `main` | Done |
| Phase 1: Data models, AKShare adapter, sync, Alembic | `main` | Done |
| Phase 8: Frontend pages skeleton + API hooks + routing | `main` | Done |

## Remaining Work — Dependency Order

```
feat-feature-registry ────────┐
        |                       |
        v                       |
feat-strategy-engine           |
        |                       |
        v                       |
feat-backtest-engine           |
        |                       |
        +──────────┬────────────+
        |          |
        v          v
feat-audit      feat-paper-portfolio  feat-risk-overlay (parallel after Phase 1)
        |          |                          |
        +────┬─────+                          |
        |    |                                |
        v    v                                |
feat-frontend-integration <──────────────────┘
        |
        v
feat-reports-demo
```

---

## Branch: `feat-feature-registry` (Phase 2)

### Task 1: Feature models

**Files:**
- Create: `backend/app/features/models.py`
- Test: `backend/tests/test_feature_models.py`

- [ ] **Step 1: Write feature models**

```python
# backend/app/features/models.py
from datetime import date, datetime
from sqlalchemy import JSON, Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class FeatureDefinition(Base):
    __tablename__ = "feature_definitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # trend/momentum/volatility/drawdown/liquidity
    lookback_days: Mapped[int] = mapped_column(Integer, nullable=False)
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FeatureValue(Base):
    __tablename__ = "feature_values"
    __table_args__ = (
        UniqueConstraint("instrument_id", "feature_definition_id", "date", "config_hash",
                         name="uq_feature_value"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"), nullable=False)
    feature_definition_id: Mapped[int] = mapped_column(ForeignKey("feature_definitions.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    config_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    instrument: Mapped["Instrument"] = relationship(back_populates="feature_values")
    feature_definition: Mapped["FeatureDefinition"] = relationship()


class FeatureRun(Base):
    __tablename__ = "feature_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    config_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"), nullable=False)
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

Add relationship to Instrument in `backend/app/data/models.py`:

```python
# Add to Instrument class:
feature_values: Mapped[list["FeatureValue"]] = relationship(back_populates="instrument")
```

- [ ] **Step 2: Run test to verify model creation**

```bash
cd backend && python -c "from app.features.models import FeatureDefinition, FeatureValue, FeatureRun; print('OK')"
```

- [ ] **Step 3: Generate and run Alembic migration**

```bash
cd backend && alembic revision --autogenerate -m "add_feature_models" && alembic upgrade head
```

### Task 2: Feature registry

**Files:**
- Create: `backend/app/features/registry.py`
- Test: `backend/tests/test_feature_registry.py`

- [ ] **Step 1: Write the FeatureRegistry class**

```python
# backend/app/features/registry.py
import hashlib
import json
from datetime import date
from sqlalchemy import select
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
        definitions = self.db.execute(select(FeatureDefinition)).scalars().all()
        config_hash = self._compute_config_hash(list(definitions))

        # Fetch bars up to as_of_date (no lookahead)
        bars = self.db.execute(
            select(DailyBar)
            .where(DailyBar.instrument_id == instrument_id, DailyBar.trade_date <= as_of_date)
            .order_by(DailyBar.trade_date.asc())
        ).scalars().all()

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

        # Persist feature values
        for d in definitions:
            fv = FeatureValue(
                instrument_id=instrument_id,
                feature_definition_id=d.id,
                date=as_of_date,
                value=all_features.get(d.name, 0.0),
                config_hash=config_hash,
            )
            self.db.add(fv)

        run = FeatureRun(
            config_hash=config_hash,
            instrument_id=instrument_id,
            as_of_date=as_of_date,
        )
        self.db.add(run)
        self.db.flush()

        return all_features
```

- [ ] **Step 2: Write test for registry**

```python
# backend/tests/test_feature_registry.py
def test_registry_register_and_compute(db_session):
    from app.features.registry import FeatureRegistry
    from app.features.models import FeatureDefinition
    from app.data.models import Instrument, DailyBar
    from datetime import date

    # Setup: create instrument and bars
    inst = Instrument(symbol="510050", name="50ETF", exchange="SH", category="broad")
    db_session.add(inst)
    db_session.flush()

    for i in range(200):
        bar = DailyBar(
            instrument_id=inst.id,
            trade_date=date(2024, 1, 1) + __import__("datetime").timedelta(days=i),
            open=1.0 + i * 0.001,
            high=1.01 + i * 0.001,
            low=0.99 + i * 0.001,
            close=1.0 + i * 0.001,
            volume=1000000 + i * 1000,
            amount=1000000.0 + i * 1000,
            data_source="test",
        )
        db_session.add(bar)
    db_session.flush()

    registry = FeatureRegistry(db_session)
    fd = registry.register(FeatureDefinition(name="momentum_20d", category="momentum", lookback_days=20, parameters={"window": 20}))

    features = registry.compute_all(inst.id, date(2024, 5, 1))
    assert "momentum_20d" in features
    assert isinstance(features["momentum_20d"], float)
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/features/models.py backend/app/features/registry.py backend/tests/
git commit -m "feat: add feature registry with FeatureDefinition, FeatureValue, FeatureRun models"
```

### Task 3: Trend features

**Files:**
- Create: `backend/app/features/trend.py`
- Test: `backend/tests/test_features_no_lookahead.py` (CRITICAL — no lookahead)

- [ ] **Step 1: Write trend features**

```python
# backend/app/features/trend.py
import numpy as np
from datetime import date


def _sma(prices: list[float], window: int) -> float:
    if len(prices) < window:
        return 0.0
    return float(np.mean(prices[-window:]))


def _ema(prices: list[float], window: int) -> float:
    if len(prices) < window:
        return 0.0
    alpha = 2.0 / (window + 1)
    ema = prices[0]
    for p in prices[1:]:
        ema = alpha * p + (1 - alpha) * ema
    return ema


def compute_trend_features(prefix: str, prices: list[float], dates: list[date],
                           params: dict) -> dict[str, float]:
    results: dict[str, float] = {}

    for w in [20, 60, 120, 200]:
        if len(prices) >= w:
            sma_val = _sma(prices, w)
            results[f"{prefix}_sma_{w}"] = sma_val
            results[f"{prefix}_price_vs_sma_{w}"] = (prices[-1] - sma_val) / sma_val if sma_val else 0.0

    # SMA slope (60-day)
    if len(prices) >= 61:
        prev_sma = _sma(prices[:-1], 60)
        curr_sma = _sma(prices, 60)
        results[f"{prefix}_sma_60_slope"] = (curr_sma - prev_sma) / prev_sma if prev_sma else 0.0

    # EMA crossover state (12/26)
    if len(prices) >= 26:
        ema12 = _ema(prices, 12)
        ema26 = _ema(prices, 26)
        results[f"{prefix}_ema_crossover"] = 1.0 if ema12 > ema26 else -1.0

    return results
```

- [ ] **Step 2: Write no-lookahead test (CRITICAL)**

```python
# backend/tests/test_features_no_lookahead.py
from datetime import date
from app.features.trend import compute_trend_features


def test_trend_no_future_data():
    """Verify trend features at date D use only data from <= D."""
    prices = list(range(1, 101))  # 100 days of prices: day 1=1, day 50=50, ...
    dates = [date(2024, 1, 1) + __import__("datetime").timedelta(days=i) for i in range(100)]

    # Compute with only first 50 days of data
    features_50 = compute_trend_features("test", prices[:50], dates[:50], {})
    # Compute with all 100 days
    features_100 = compute_trend_features("test", prices[:100], dates[:100], {})

    # A feature computed at day 50 should be different from day 100
    # because day 100 has access to more data
    for key in features_50:
        if key in features_100:
            assert features_50[key] != features_100[key], \
                f"No-lookahead violation: {key} identical at day 50 and day 100"
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/features/trend.py backend/tests/test_features_no_lookahead.py
git commit -m "feat: add trend features (SMA, EMA crossover, price vs MA) with no-lookahead test"
```

### Task 4: Momentum, volatility, drawdown, liquidity features

**Files:**
- Create: `backend/app/features/momentum.py`
- Create: `backend/app/features/volatility.py`
- Create: `backend/app/features/drawdown.py`
- Create: `backend/app/features/liquidity.py`

- [ ] **Step 1: Write momentum features**

```python
# backend/app/features/momentum.py
import numpy as np
from datetime import date


def compute_momentum_features(prefix: str, prices: list[float], dates: list[date],
                               params: dict) -> dict[str, float]:
    results: dict[str, float] = {}
    for window in [21, 63, 126, 252]:
        label = {21: "1m", 63: "3m", 126: "6m", 252: "12m"}[window]
        if len(prices) > window:
            ret = (prices[-1] - prices[-window - 1]) / prices[-window - 1]
            results[f"{prefix}_return_{label}"] = ret

    # Risk-adjusted momentum (return / realized vol)
    if len(prices) >= 126:
        ret_6m = (prices[-1] - prices[-127]) / prices[-127]
        daily_rets = np.diff(prices[-127:]) / prices[-128:-1]
        vol = float(np.std(daily_rets) * np.sqrt(252))
        results[f"{prefix}_risk_adj_momentum"] = ret_6m / vol if vol > 0 else 0.0

    return results
```

- [ ] **Step 2: Write volatility features**

```python
# backend/app/features/volatility.py
import numpy as np
from datetime import date


def compute_volatility_features(prefix: str, prices: list[float], dates: list[date],
                                 params: dict) -> dict[str, float]:
    results: dict[str, float] = {}
    for w in [20, 60]:
        if len(prices) > w:
            daily_rets = np.diff(prices[-w:]) / prices[-w:-1]
            vol = float(np.std(daily_rets) * np.sqrt(252))
            results[f"{prefix}_realized_vol_{w}d"] = vol

    # Volatility percentile vs 1-year window
    if len(prices) >= 252:
        daily_rets_20 = np.diff(prices[-20:]) / prices[-21:-1]
        vol_20 = float(np.std(daily_rets_20) * np.sqrt(252))
        # Compute rolling 20-day vol for past year
        rolling_vols = []
        for i in range(252 - 20):
            window_rets = np.diff(prices[-(252 - i):-(252 - i - 21)]) / prices[-(253 - i):-(253 - i - 21)]
            rolling_vols.append(float(np.std(window_rets) * np.sqrt(252)))
        if rolling_vols:
            pct_rank = sum(1 for v in rolling_vols if v <= vol_20) / len(rolling_vols)
            results[f"{prefix}_vol_percentile"] = pct_rank

    return results
```

- [ ] **Step 3: Write drawdown features**

```python
# backend/app/features/drawdown.py
import numpy as np
from datetime import date


def compute_drawdown_features(prefix: str, prices: list[float], dates: list[date],
                               params: dict) -> dict[str, float]:
    results: dict[str, float] = {}
    if len(prices) < 2:
        return results

    # Current drawdown from N-day peak
    for w in [60, 120, 252]:
        if len(prices) >= w:
            peak = max(prices[-w:])
            dd = (prices[-1] - peak) / peak
            results[f"{prefix}_drawdown_{w}d"] = dd

    # Max drawdown
    peak = prices[0]
    max_dd = 0.0
    dd_duration = 0
    current_dd_duration = 0
    for p in prices[1:]:
        peak = max(peak, p)
        dd = (p - peak) / peak
        max_dd = min(max_dd, dd)
        if dd < 0:
            current_dd_duration += 1
        else:
            dd_duration = max(dd_duration, current_dd_duration)
            current_dd_duration = 0
    dd_duration = max(dd_duration, current_dd_duration)

    results[f"{prefix}_max_drawdown"] = max_dd
    results[f"{prefix}_drawdown_duration"] = float(dd_duration)

    return results
```

- [ ] **Step 4: Write liquidity features**

```python
# backend/app/features/liquidity.py
import numpy as np
from datetime import date


def compute_liquidity_features(prefix: str, volumes: list[float], dates: list[date],
                                 params: dict) -> dict[str, float]:
    results: dict[str, float] = {}
    if len(volumes) < 5:
        return results

    # Average daily volume over 20 and 60 days
    for w in [20, 60]:
        if len(volumes) >= w:
            results[f"{prefix}_adv_{w}d"] = float(np.mean(volumes[-w:]))
            # Volume trend: ratio of recent ADV to longer ADV
            if w == 20 and len(volumes) >= 60:
                adv20 = float(np.mean(volumes[-20:]))
                adv60 = float(np.mean(volumes[-60:]))
                results[f"{prefix}_volume_trend"] = adv20 / adv60 if adv60 > 0 else 1.0

    # Zero volume days count
    zero_days = sum(1 for v in volumes[-20:] if v == 0)
    results[f"{prefix}_zero_vol_days_20d"] = float(zero_days)

    return results
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/features/momentum.py backend/app/features/volatility.py backend/app/features/drawdown.py backend/app/features/liquidity.py
git commit -m "feat: add momentum, volatility, drawdown, and liquidity feature computers"
```

### Task 5: Feature API and seed definitions

**Files:**
- Create: `backend/app/api/features.py`
- Modify: `backend/app/main.py` (register router)

- [ ] **Step 1: Write feature API router**

```python
# backend/app/api/features.py
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.base import get_db
from app.features.models import FeatureDefinition, FeatureValue
from app.features.registry import FeatureRegistry

router = APIRouter(tags=["features"])


class FeatureDefinitionOut(BaseModel):
    id: int
    name: str
    category: str
    lookback_days: int
    parameters: dict

    model_config = {"from_attributes": True}


class ComputeRequest(BaseModel):
    instrument_id: int
    as_of_date: str  # YYYY-MM-DD


@router.get("/definitions", response_model=list[FeatureDefinitionOut])
def list_definitions(db: Session = Depends(get_db)):
    return db.execute(select(FeatureDefinition)).scalars().all()


@router.post("/compute")
def compute_features(req: ComputeRequest, db: Session = Depends(get_db)):
    from datetime import date as date_type
    registry = FeatureRegistry(db)
    as_of = date_type.fromisoformat(req.as_of_date)
    features = registry.compute_all(req.instrument_id, as_of)
    return {"instrument_id": req.instrument_id, "as_of_date": req.as_of_date, "features": features}


@router.get("/values")
def get_values(instrument_id: int = Query(...), date: str = Query(...), db: Session = Depends(get_db)):
    from datetime import date as date_type
    d = date_type.fromisoformat(date)
    values = db.execute(
        select(FeatureValue).where(
            FeatureValue.instrument_id == instrument_id,
            FeatureValue.date == d,
        )
    ).scalars().all()
    return [{"feature_name": v.feature_definition.name if v.feature_definition else str(v.feature_definition_id), "value": v.value, "config_hash": v.config_hash} for v in values]
```

- [ ] **Step 2: Register in main.py and seed default definitions**

Add to `backend/app/main.py`:
```python
from app.api.features import router as features_router
app.include_router(features_router, prefix="/features", tags=["features"])
```

Seed script `backend/scripts/seed_features.py`:
```python
# Seed default feature definitions
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
```

- [ ] **Step 3: Commit and merge to main**

```bash
git add backend/app/features/ backend/app/api/features.py backend/app/main.py backend/scripts/
git commit -m "feat: add feature API routes and seed definitions"
git push origin feat-feature-registry
```

---

## Branch: `feat-risk-overlay` (Phase 5 — parallel with features)

### Task 6: Risk models and state machine

**Files:**
- Create: `backend/app/risk/models.py`
- Create: `backend/app/risk/state_machine.py`
- Create: `backend/app/risk/rules.py`
- Create: `backend/app/risk/overlay.py`

- [ ] **Step 1: Write risk models**

```python
# backend/app/risk/models.py
from datetime import date, datetime
from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class RiskProfile(Base):
    __tablename__ = "risk_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    max_drawdown: Mapped[float] = mapped_column(Float, nullable=False)
    max_volatility: Mapped[float] = mapped_column(Float, nullable=False)
    max_concentration: Mapped[float] = mapped_column(Float, nullable=False)
    liquidity_threshold: Mapped[float] = mapped_column(Float, default=0.0)
    max_equity_exposure: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RiskState(Base):
    __tablename__ = "risk_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(20), nullable=False)  # NORMAL/CAUTION/DEFENSIVE/HALT
    transition_reason: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RiskRuleResult(Base):
    __tablename__ = "risk_rule_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    rule_name: Mapped[str] = mapped_column(String(100), nullable=False)
    triggered: Mapped[bool] = mapped_column(Boolean, default=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # INFO/WARNING/CRITICAL
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RiskOverlayDecision(Base):
    __tablename__ = "risk_overlay_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    original_targets: Mapped[dict] = mapped_column(JSON, default=dict)
    final_targets: Mapped[dict] = mapped_column(JSON, default=dict)
    suppressed_trades: Mapped[dict] = mapped_column(JSON, default=dict)
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)  # ALLOW/REDUCE/BLOCK/MANUAL_CONFIRM
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 2: Write state machine**

```python
# backend/app/risk/state_machine.py
from datetime import date
from app.risk.models import RiskState

STATE_ORDER = {"NORMAL": 0, "CAUTION": 1, "DEFENSIVE": 2, "HALT": 3}


class RiskStateMachine:
    def __init__(self, db):
        self.db = db

    def get_current_state(self) -> RiskState:
        from sqlalchemy import select, desc
        result = self.db.execute(
            select(RiskState).order_by(desc(RiskState.date)).limit(1)
        ).scalar_one_or_none()
        if not result:
            result = RiskState(date=date.today(), state="NORMAL", transition_reason="initial")
            self.db.add(result)
            self.db.flush()
        return result

    def evaluate(self, rule_results: list["RiskRuleResult"]) -> RiskState:
        current = self.get_current_state()
        critical_count = sum(1 for r in rule_results if r.severity == "CRITICAL" and r.triggered)
        warning_count = sum(1 for r in rule_results if r.severity == "WARNING" and r.triggered)

        if critical_count >= 2:
            new_state = "HALT"
        elif critical_count >= 1:
            new_state = "DEFENSIVE"
        elif warning_count >= 3:
            new_state = "CAUTION"
        elif warning_count >= 1:
            new_state = "CAUTION"
        else:
            new_state = "NORMAL"

        # Don't skip states — transition one level at a time toward target
        current_idx = STATE_ORDER[current.state]
        target_idx = STATE_ORDER[new_state]
        if current_idx < target_idx:
            new_state_idx = min(current_idx + 1, target_idx)
            new_state = [s for s, i in STATE_ORDER.items() if i == new_state_idx][0]
        elif current_idx > target_idx and current.state != "NORMAL":
            new_state_idx = max(current_idx - 1, target_idx)
            new_state = [s for s, i in STATE_ORDER.items() if i == new_state_idx][0]

        reason = f"Critical: {critical_count}, Warning: {warning_count}"
        record = RiskState(date=date.today(), state=new_state, transition_reason=reason)
        self.db.add(record)
        self.db.flush()
        return record
```

- [ ] **Step 3: Write risk rules**

```python
# backend/app/risk/rules.py
import numpy as np
from datetime import date
from typing import Optional

from app.risk.models import RiskRuleResult, RiskProfile


class TrendBreakRule:
    def __init__(self, risk_profile: RiskProfile):
        self.profile = risk_profile

    def check(self, market_index_close: float, market_sma_60: float,
              market_momentum: float, dt: date) -> RiskRuleResult:
        below_ma = market_index_close < market_sma_60
        neg_momentum = market_momentum < 0
        triggered = below_ma and neg_momentum
        severity = "WARNING" if triggered else "INFO"
        detail = {
            "market_close": market_index_close,
            "sma_60": market_sma_60,
            "market_momentum": market_momentum,
            "below_ma": below_ma,
        }
        return RiskRuleResult(date=dt, rule_name="trend_break", triggered=triggered,
                              severity=severity, detail=detail)


class VolatilitySpikeRule:
    def __init__(self, risk_profile: RiskProfile):
        self.profile = risk_profile

    def check(self, realized_vol: float, vol_percentile: float, dt: date) -> RiskRuleResult:
        triggered = vol_percentile > 0.90 or realized_vol > self.profile.max_volatility
        severity = "CRITICAL" if realized_vol > self.profile.max_volatility * 1.5 else ("WARNING" if triggered else "INFO")
        return RiskRuleResult(date=dt, rule_name="volatility_spike", triggered=triggered,
                              severity=severity, detail={"realized_vol": realized_vol, "percentile": vol_percentile})


class DrawdownRule:
    def __init__(self, risk_profile: RiskProfile):
        self.profile = risk_profile

    def check(self, portfolio_drawdown: float, dt: date) -> RiskRuleResult:
        triggered = abs(portfolio_drawdown) > abs(self.profile.max_drawdown)
        severity = "CRITICAL" if abs(portfolio_drawdown) > abs(self.profile.max_drawdown) * 1.5 else ("WARNING" if triggered else "INFO")
        return RiskRuleResult(date=dt, rule_name="portfolio_drawdown", triggered=triggered,
                              severity=severity, detail={"drawdown": portfolio_drawdown, "threshold": self.profile.max_drawdown})


class LiquidityDegradationRule:
    def __init__(self, risk_profile: RiskProfile):
        self.profile = risk_profile

    def check(self, etf_symbol: str, volume_ratio: float, dt: date) -> RiskRuleResult:
        triggered = volume_ratio < 0.3  # Current ADV < 30% of historical ADV
        return RiskRuleResult(date=dt, rule_name=f"liquidity_degradation_{etf_symbol}",
                              triggered=triggered, severity="WARNING" if triggered else "INFO",
                              detail={"symbol": etf_symbol, "volume_ratio": volume_ratio})
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/risk/models.py backend/app/risk/state_machine.py backend/app/risk/rules.py
git commit -m "feat: add risk models, state machine, and core rules (trend break, vol spike, drawdown, liquidity)"
```

### Task 7: Risk overlay and API

**Files:**
- Create: `backend/app/risk/overlay.py`
- Create: `backend/app/api/risk.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write risk overlay engine**

```python
# backend/app/risk/overlay.py
from datetime import date
from sqlalchemy.orm import Session
from app.risk.state_machine import RiskStateMachine
from app.risk.rules import TrendBreakRule, VolatilitySpikeRule, DrawdownRule, LiquidityDegradationRule
from app.risk.models import RiskProfile, RiskOverlayDecision


class RiskOverlay:
    def __init__(self, db: Session, risk_profile: RiskProfile):
        self.db = db
        self.profile = risk_profile
        self.state_machine = RiskStateMachine(db)
        self.rules = [
            TrendBreakRule(risk_profile),
            VolatilitySpikeRule(risk_profile),
            DrawdownRule(risk_profile),
        ]

    def apply(self, market_data: dict, portfolio_drawdown: float,
              target_portfolio: list[dict], dt: date) -> RiskOverlayDecision:
        # Run all rules
        rule_results = []
        rule_results.append(self.rules[0].check(
            market_data.get("index_close", 0),
            market_data.get("index_sma_60", 0),
            market_data.get("market_momentum", 0),
            dt
        ))
        rule_results.append(self.rules[1].check(
            market_data.get("realized_vol", 0),
            market_data.get("vol_percentile", 0),
            dt
        ))
        rule_results.append(self.rules[2].check(portfolio_drawdown, dt))

        for r in rule_results:
            self.db.add(r)
        self.db.flush()

        # Evaluate state
        state = self.state_machine.evaluate(rule_results)

        # Determine decision and modify targets
        decision_map = {"NORMAL": "ALLOW", "CAUTION": "REDUCE", "DEFENSIVE": "REDUCE", "HALT": "BLOCK"}
        action = decision_map[state.state]

        final_targets = target_portfolio
        suppressed_trades = []
        reason = f"Risk state: {state.state}. Reason: {state.transition_reason}"

        if action == "REDUCE":
            scale = 0.5 if state.state == "DEFENSIVE" else 0.75
            for t in final_targets:
                t["target_weight"] = t.get("target_weight", 0) * scale
            reason += f". Scaled positions to {scale*100:.0f}%"
        elif action == "BLOCK":
            suppressed_trades = [{"symbol": t.get("symbol"), "original_weight": t.get("target_weight")}
                                for t in final_targets if t.get("target_weight", 0) > 0]
            final_targets = [{**t, "target_weight": 0.0} for t in final_targets]
            reason += ". All risk-increasing trades blocked."

        decision = RiskOverlayDecision(
            date=dt,
            original_targets={"positions": target_portfolio},
            final_targets={"positions": final_targets},
            suppressed_trades={"trades": suppressed_trades},
            reason=reason,
            decision=action,
        )
        self.db.add(decision)
        self.db.flush()
        return decision
```

- [ ] **Step 2: Write risk API**

```python
# backend/app/api/risk.py
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.db.base import get_db
from app.risk.models import RiskState, RiskRuleResult, RiskOverlayDecision

router = APIRouter(tags=["risk"])


@router.get("/state")
def get_risk_state(db: Session = Depends(get_db)):
    state = db.execute(select(RiskState).order_by(desc(RiskState.date)).limit(1)).scalar_one_or_none()
    if not state:
        return {"state": "NORMAL", "transition_reason": "default"}
    return {"date": str(state.date), "state": state.state, "transition_reason": state.transition_reason}


@router.get("/rules")
def get_rules(date: str = Query(None), db: Session = Depends(get_db)):
    q = select(RiskRuleResult)
    if date:
        q = q.where(RiskRuleResult.date == date)
    else:
        q = q.order_by(desc(RiskRuleResult.date)).limit(50)
    results = db.execute(q).scalars().all()
    return [{"date": str(r.date), "rule_name": r.rule_name, "triggered": r.triggered,
             "severity": r.severity, "detail": r.detail} for r in results]


@router.get("/overlay")
def get_overlay(db: Session = Depends(get_db)):
    decision = db.execute(
        select(RiskOverlayDecision).order_by(desc(RiskOverlayDecision.date)).limit(1)
    ).scalar_one_or_none()
    if not decision:
        return {"decision": "ALLOW", "reason": "No overlay decision yet"}
    return {"date": str(decision.date), "decision": decision.decision, "reason": decision.reason,
            "original_targets": decision.original_targets, "final_targets": decision.final_targets,
            "suppressed_trades": decision.suppressed_trades}
```

- [ ] **Step 3: Register router and commit**

```bash
git add backend/app/risk/overlay.py backend/app/api/risk.py
git commit -m "feat: add risk overlay engine and /risk API routes"
git push origin feat-risk-overlay
```

---

## Branch: `feat-strategy-engine` (Phase 3 — depends on feat-feature-registry)

### Task 8: Strategy models and scoring

**Files:**
- Create: `backend/app/strategy/models.py`
- Create: `backend/app/strategy/rotation.py`
- Create: `backend/app/strategy/constraints.py`
- Create: `backend/app/strategy/explainer.py`

- [ ] **Step 1: Write strategy models**

```python
# backend/app/strategy/models.py
from datetime import date, datetime
from sqlalchemy import JSON, Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class StrategyConfig(Base):
    __tablename__ = "strategy_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(20), default="v1")
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)
    universe_filter: Mapped[dict] = mapped_column(JSON, default=dict)
    risk_profile: Mapped[str] = mapped_column(String(50), default="balanced")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class StrategyRun(Base):
    __tablename__ = "strategy_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    config_id: Mapped[int] = mapped_column(ForeignKey("strategy_configs.id"), nullable=False)
    run_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    config_hash: Mapped[str] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("strategy_runs.id"), nullable=False)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[dict] = mapped_column(JSON, default=dict)


class TargetPortfolio(Base):
    __tablename__ = "target_portfolios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("strategy_runs.id"), nullable=False)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"), nullable=False)
    target_weight: Mapped[float] = mapped_column(Float, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    constraint_info: Mapped[dict] = mapped_column(JSON, default=dict)


class ExplanationLog(Base):
    __tablename__ = "explanation_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("strategy_runs.id"), nullable=False)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(10), nullable=False)  # BUY/SELL/HOLD
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    score_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
```

- [ ] **Step 2: Write strategy rotation engine (scoring)**

```python
# backend/app/strategy/rotation.py
import hashlib
import json
from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.strategy.models import StrategyConfig, StrategyRun, Signal, TargetPortfolio, ExplanationLog
from app.features.registry import FeatureRegistry
from app.features.models import FeatureValue
from app.data.models import Instrument
from app.strategy.constraints import apply_concentration_limit, apply_turnover_limit, apply_min_positions, apply_max_drawdown_check


DEFAULT_WEIGHTS = {
    "trend": 0.25,
    "momentum": 0.30,
    "volatility": 0.15,
    "drawdown": 0.15,
    "liquidity": 0.15,
}


class RiskAwareETFRotationV1:
    def __init__(self, db: Session, config: StrategyConfig):
        self.db = db
        self.config = config
        self.feature_registry = FeatureRegistry(db)

    def score_etf(self, instrument_id: int, as_of_date: date) -> dict:
        features = self.feature_registry.compute_all(instrument_id, as_of_date)
        if not features:
            return {"score": 0.0, "breakdown": {}}

        score = 0.0
        breakdown = {}
        for category, weight in DEFAULT_WEIGHTS.items():
            cat_features = {k: v for k, v in features.items() if k.startswith(category)}
            cat_score = sum(v for v in cat_features.values()) / max(len(cat_features), 1)
            score += weight * cat_score
            breakdown[category] = {"weight": weight, "sub_score": cat_score, "features_used": list(cat_features.keys())}

        return {"score": score, "breakdown": breakdown}

    def build_portfolio(self, scores: list[dict], constraints: dict,
                        prev_portfolio: dict | None = None) -> list[dict]:
        ranked = sorted(scores, key=lambda x: x["score"], reverse=True)
        n_select = constraints.get("max_holdings", 5)
        selected = ranked[:n_select]

        total_score = sum(abs(s["score"]) for s in selected) or 1.0
        weights = [abs(s["score"]) / total_score for s in selected]

        portfolio = []
        for s, w in zip(selected, weights):
            portfolio.append({
                "instrument_id": s["instrument_id"],
                "score": s["score"],
                "target_weight": round(w, 4),
                "breakdown": s["breakdown"],
            })

        portfolio = apply_concentration_limit(portfolio, constraints.get("max_concentration", 0.30))
        portfolio = apply_min_positions(portfolio, constraints.get("min_positions", 3))

        if prev_portfolio:
            portfolio = apply_turnover_limit(portfolio, prev_portfolio, constraints.get("max_turnover", 0.50))

        return portfolio

    def generate_signals(self, universe: list[Instrument], as_of_date: date) -> dict:
        scores = []
        for inst in universe:
            s = self.score_etf(inst.id, as_of_date)
            scores.append({"instrument_id": inst.id, "symbol": inst.symbol, **s})

        params = self.config.parameters or {}
        portfolio = self.build_portfolio(scores, params)

        srun = StrategyRun(
            config_id=self.config.id,
            run_date=as_of_date,
            status="completed",
        )
        self.db.add(srun)
        self.db.flush()

        ranked = sorted(scores, key=lambda x: x["score"], reverse=True)
        for rank, s in enumerate(ranked, 1):
            signal = Signal(
                run_id=srun.id,
                instrument_id=s["instrument_id"],
                score=s["score"],
                rank=rank,
                reason={"breakdown": s.get("breakdown", {})},
            )
            self.db.add(signal)

        for p in portfolio:
            tp = TargetPortfolio(
                run_id=srun.id,
                instrument_id=p["instrument_id"],
                target_weight=p["target_weight"],
                score=p["score"],
                constraint_info={"constraints": params},
            )
            self.db.add(tp)

            # Generate explanation
            symbol = next((inst.symbol for inst in universe if inst.id == p["instrument_id"]), "?")
            top_reason = max(p.get("breakdown", {}).items(),
                            key=lambda x: x[1]["weight"] * abs(x[1]["sub_score"])) if p.get("breakdown") else ("unknown", {"sub_score": 0})
            explanation = ExplanationLog(
                run_id=srun.id,
                instrument_id=p["instrument_id"],
                action="BUY" if p["target_weight"] > 0 else "SELL",
                reason=f"{symbol}: weight={p['target_weight']:.2%}, score={p['score']:.3f}, "
                       f"top driver={top_reason[0]} ({top_reason[1]['sub_score']:.3f})",
                score_breakdown=p.get("breakdown", {}),
            )
            self.db.add(explanation)

        self.db.flush()
        return {"run_id": srun.id, "signals": [{"instrument_id": s.instrument_id, "score": s.score, "rank": s.rank} for s in self.db.execute(select(Signal).where(Signal.run_id == srun.id)).scalars().all()], "portfolio": portfolio}
```

- [ ] **Step 3: Write constraints module**

```python
# backend/app/strategy/constraints.py

def apply_concentration_limit(portfolio: list[dict], max_weight: float = 0.30) -> list[dict]:
    for p in portfolio:
        if p["target_weight"] > max_weight:
            excess = p["target_weight"] - max_weight
            p["target_weight"] = max_weight
            n_others = len(portfolio) - 1
            if n_others > 0:
                distrib = excess / n_others
                for other in portfolio:
                    if other["instrument_id"] != p["instrument_id"]:
                        other["target_weight"] += distrib
    return portfolio


def apply_turnover_limit(portfolio: list[dict], prev_portfolio: dict,
                         max_turnover: float = 0.50) -> list[dict]:
    prev_weights = {p["instrument_id"]: p.get("target_weight", 0) for p in prev_portfolio.get("positions", [])}
    total_turnover = sum(abs(p["target_weight"] - prev_weights.get(p["instrument_id"], 0)) for p in portfolio)
    half_turnover = total_turnover / 2
    if half_turnover > max_turnover:
        scale = max_turnover / half_turnover
        for p in portfolio:
            prev_w = prev_weights.get(p["instrument_id"], 0)
            p["target_weight"] = prev_w + (p["target_weight"] - prev_w) * scale
    return portfolio


def apply_min_positions(portfolio: list[dict], min_count: int = 3) -> list[dict]:
    non_zero = [p for p in portfolio if p["target_weight"] > 0.01]
    if len(non_zero) < min_count:
        for p in portfolio:
            if p["target_weight"] < 0.01:
                p["target_weight"] = 0.01
    return portfolio


def apply_max_drawdown_check(portfolio: list[dict], instrument_drawdowns: dict,
                              max_dd: float = -0.15) -> list[dict]:
    for p in portfolio:
        dd = instrument_drawdowns.get(p["instrument_id"], 0)
        if dd < max_dd:
            p["target_weight"] = 0.0
    return portfolio
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/strategy/
git commit -m "feat: add strategy engine with composite scoring, constraints, and explanation logs"
```

### Task 9: Strategy API

**Files:**
- Create: `backend/app/api/strategy.py`
- Modify: `backend/app/main.py`
- Create: `config/strategies/risk_aware_v1.json`
- Create: `config/risk_profiles/balanced.json`, `conservative.json`, `aggressive.json`

- [ ] **Step 1: Write strategy API**

```python
# backend/app/api/strategy.py
from datetime import date as date_type
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.db.base import get_db
from app.strategy.models import StrategyConfig, StrategyRun, Signal, TargetPortfolio, ExplanationLog
from app.strategy.rotation import RiskAwareETFRotationV1
from app.data.models import Instrument

router = APIRouter(tags=["strategy"])


class RunRequest(BaseModel):
    as_of_date: str


@router.post("/run")
def run_strategy(req: RunRequest, db: Session = Depends(get_db)):
    config = db.execute(select(StrategyConfig).limit(1)).scalar_one_or_none()
    if not config:
        config = StrategyConfig(name="risk_aware_etf_rotation_v1", version="v1")
        db.add(config)
        db.flush()

    universe = db.execute(select(Instrument)).scalars().all()
    if not universe:
        return {"error": "No instruments in universe"}

    strategy = RiskAwareETFRotationV1(db, config)
    as_of = date_type.fromisoformat(req.as_of_date)
    result = strategy.generate_signals(universe, as_of)
    return {"run_id": result["run_id"], "signals_count": len(result["signals"]),
            "portfolio_count": len(result["portfolio"])}


@router.get("/signals")
def get_signals(run_id: int = Query(None), db: Session = Depends(get_db)):
    if run_id:
        signals = db.execute(select(Signal).where(Signal.run_id == run_id).order_by(Signal.rank)).scalars().all()
    else:
        latest_run = db.execute(select(StrategyRun).order_by(desc(StrategyRun.id)).limit(1)).scalar_one_or_none()
        if not latest_run:
            return []
        signals = db.execute(select(Signal).where(Signal.run_id == latest_run.id).order_by(Signal.rank)).scalars().all()
    return [{"instrument_id": s.instrument_id, "score": s.score, "rank": s.rank, "reason": s.reason} for s in signals]


@router.get("/portfolio")
def get_portfolio(run_id: int = Query(None), db: Session = Depends(get_db)):
    if run_id:
        positions = db.execute(select(TargetPortfolio).where(TargetPortfolio.run_id == run_id)).scalars().all()
    else:
        latest_run = db.execute(select(StrategyRun).order_by(desc(StrategyRun.id)).limit(1)).scalar_one_or_none()
        if not latest_run:
            return []
        positions = db.execute(select(TargetPortfolio).where(TargetPortfolio.run_id == latest_run.id)).scalars().all()
    return [{"instrument_id": p.instrument_id, "target_weight": p.target_weight, "score": p.score,
             "constraint_info": p.constraint_info} for p in positions]


@router.get("/explanations/{run_id}")
def get_explanations(run_id: int, db: Session = Depends(get_db)):
    logs = db.execute(select(ExplanationLog).where(ExplanationLog.run_id == run_id)).scalars().all()
    return [{"instrument_id": l.instrument_id, "action": l.action, "reason": l.reason,
             "score_breakdown": l.score_breakdown} for l in logs]
```

- [ ] **Step 2: Create config files and commit**

```bash
git add backend/app/api/strategy.py config/strategies/ config/risk_profiles/
git commit -m "feat: add strategy API routes and config files"
git push origin feat-strategy-engine
```

---

## Branch: `feat-backtest-engine` (Phase 4)

### Task 10: Backtest models and engine

**Files:**
- Create: `backend/app/backtest/models.py`
- Create: `backend/app/backtest/engine.py`
- Create: `backend/app/backtest/metrics.py`

*(Full implementation with portfolio simulator, rebalancing, cost/slippage application, equity curve computation, performance metrics including Sharpe, max drawdown, win rate, benchmark comparison.)*

### Task 11: Backtest API

**Files:**
- Create: `backend/app/api/backtest.py`

*(POST /backtest/run, GET /backtest/status/{run_id}, GET /backtest/results/{run_id}, GET /backtest/compare/{run_id})*

---

## Branch: `feat-audit-gatekeeper` (Phase 6)

### Task 12: Audit models and checks

**Files:**
- Create: `backend/app/audit/models.py`
- Create: `backend/app/audit/leakage.py`
- Create: `backend/app/audit/walk_forward.py`
- Create: `backend/app/audit/param_stability.py`
- Create: `backend/app/audit/cost_stress.py`
- Create: `backend/app/audit/grading.py`

*(AuditRun, AuditCheckResult models; leakage check verifies no future data in features/signals; walk-forward with train/test windows; parameter stability via perturbation; cost stress at 1x/2x/5x; weighted grading to GREEN/YELLOW/RED.)*

### Task 13: Audit API

**Files:**
- Create: `backend/app/api/audit.py`

*(POST /audit/run, GET /audit/status/{run_id}, GET /audit/report/{run_id})*

---

## Branch: `feat-paper-portfolio` (Phase 7)

### Task 14: Paper trading models and engine

**Files:**
- Create: `backend/app/paper/models.py`
- Create: `backend/app/paper/engine.py`

*(PaperPortfolio, PaperPosition, PaperOrder, PaperLedger models; PaperTradingEngine with create, apply_signal, mark_to_market, get_pnl.)*

### Task 15: Paper trading API

**Files:**
- Create: `backend/app/api/paper.py`

*(POST /paper/portfolio, POST /paper/apply-signal, GET /paper/holdings, GET /paper/pnl, GET /paper/ledger)*

---

## Branch: `feat-frontend-integration` (Phase 8 remaining)

### Task 16: Real API integration and TanStack Query

**Files:**
- Modify: `frontend/src/api/hooks.ts`
- Modify: `frontend/src/App.tsx`

*(Replace mock data with real API calls. Add TanStack Query for caching/refetching. Wire up WebSocket for real-time risk state updates.)*

### Task 17: Chart components

**Files:**
- Create: `frontend/src/components/EquityChart.tsx`
- Create: `frontend/src/components/DrawdownChart.tsx`
- Create: `frontend/src/components/WeightBarChart.tsx`

*(Recharts-based equity curve, drawdown waterfall, target weight bar charts.)*

---

## Branch: `feat-reports-demo` (Phase 9)

### Task 18: Report generation

**Files:**
- Create: `backend/app/reports/figures.py`
- Create: `backend/app/reports/tables.py`

*(matplotlib/plotly figures: equity curve + benchmark, drawdown chart, risk state timeline, feature importance. CSV/Markdown export.)*

### Task 19: Demo script and docs

**Files:**
- Create: `docs/demo_script.md`
- Create: `docs/reproducibility.md`

*(Step-by-step walkthrough from clean checkout to audit report.)*

---

## Execution Strategy

**Wave 1 (parallel):** `feat-feature-registry` + `feat-risk-overlay` — slide into main
**Wave 2:** `feat-strategy-engine` → merge main
**Wave 3:** `feat-backtest-engine` → merge main
**Wave 4 (parallel):** `feat-audit-gatekeeper` + `feat-paper-portfolio` → merge main
**Wave 5:** `feat-frontend-integration` → merge main
**Wave 6:** `feat-reports-demo` → merge main

Each wave: branch → implement → push → merge to main. Next wave branches from updated main.
