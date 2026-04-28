# Test & Optimize Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 3 remaining API failures (strategy UniqueViolation, backtest FK, audit FK), add proper empty states to all frontend pages, ensure end-to-end user flow works

**Architecture:** Strategy fails because FeatureRegistry re-inserts existing values → need upsert. Backtest/Audit fail because strategy/backtest configs referenced by hardcoded ID don't exist → need idempotent lookup-or-create in endpoints. Frontend pages crash on empty data → need defensive rendering.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.x, React + TypeScript

---

## Diagnosed Issues

| # | Endpoint | Error | Root Cause |
|---|----------|-------|------------|
| 1 | `POST /strategy/run` | 500 UniqueViolation | FeatureRegistry inserts duplicate feature values |
| 2 | `POST /backtest/run` | 500 FK violation | `strategy_config_id=1` hardcoded, doesn't exist |
| 3 | `POST /audit/run` | 500 FK violation | `backtest_config_id=1` hardcoded, doesn't exist |
| 4 | Signals page | misrender | Uses old signal shape expectations |
| 5 | Backtest page | empty | No "run first" empty state |
| 6 | Audit page | empty | No "run first" empty state |

---

## Task 1: Fix FeatureRegistry upsert for idempotent compute

**Files:**
- Modify: `backend/app/features/registry.py`

**Root cause:** `compute_all()` inserts new FeatureValue rows without checking for existing (instrument_id, feature_definition_id, date, config_hash) combinations.

**Fix:** Change FeatureValue insertion to use PostgreSQL ON CONFLICT DO NOTHING or DO UPDATE.

```python
# In compute_all(), replace:
for d in definitions:
    fv = FeatureValue(
        instrument_id=instrument_id,
        feature_definition_id=d.id,
        date=as_of_date,
        value=all_features.get(d.name, 0.0),
        config_hash=config_hash,
    )
    self.db.add(fv)

# With:
from sqlalchemy.dialects.postgresql import insert as pg_insert
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
```

**Verify:**
```bash
curl -X POST localhost:8001/features/compute -H "Content-Type: application/json" -d '{"instrument_id":7,"as_of_date":"2025-10-28"}'
curl -X POST localhost:8001/features/compute -H "Content-Type: application/json" -d '{"instrument_id":7,"as_of_date":"2025-10-28"}'
# Both should return 200
curl -X POST localhost:8001/strategy/run -H "Content-Type: application/json" -d '{"as_of_date":"2025-10-28"}'
# Should return 200
```

---

## Task 2: Fix Backtest endpoint — lookup or create strategy config

**Files:**
- Modify: `backend/app/api/backtest.py`

**Root cause:** Hardcoded `strategy_config_id=1` in the request default and no fallback to create it.

**Fix:** Look up existing StrategyConfig or create one.

```python
@router.post("/run")
def run_backtest(req: BacktestConfigRequest, db: Session = Depends(get_db)):
    # Look up or create strategy config
    strat_cfg = db.execute(
        select(StrategyConfig).where(StrategyConfig.id == req.strategy_config_id)
    ).scalar_one_or_none()
    if not strat_cfg:
        strat_cfg = StrategyConfig(
            name="risk_aware_etf_rotation_v1", version="v1",
            parameters={"max_holdings": 5, "max_concentration": 0.30,
                       "min_positions": 3, "max_turnover": 0.50},
        )
        db.add(strat_cfg)
        db.flush()
        # Update request to use the new config ID
        req.strategy_config_id = strat_cfg.id

    config = BacktestConfig(
        strategy_config_id=req.strategy_config_id,
        ...
    )
    ...
```

- Add import: `from app.strategy.models import StrategyConfig`

**Verify:**
```bash
curl -X POST localhost:8001/backtest/run -H "Content-Type: application/json" -d '{"start_date":"2025-01-01","end_date":"2025-10-28","initial_capital":100000}'
# Should return 200 with run_id
curl localhost:8001/backtest/results/1 | python3 -c "import sys,json;d=json.load(sys.stdin);print(len(d.get('equity_curve',[])),'equity points')"
```

---

## Task 3: Fix Audit endpoint — lookup or create backtest config

**Files:**
- Modify: `backend/app/api/audit.py`

**Root cause:** Hardcoded `backtest_config_id=1` with no fallback.

**Fix:** Look up or create.

```python
@router.post("/run")
def run_audit(req: AuditRequest, db: Session = Depends(get_db)):
    # Look up or create backtest config
    btc = db.execute(
        select(BacktestConfig).where(BacktestConfig.id == req.backtest_config_id)
    ).scalar_one_or_none()
    if not btc:
        # Ensure strategy config exists
        strat_cfg = db.execute(
            select(StrategyConfig).limit(1)
        ).scalar_one_or_none()
        if not strat_cfg:
            strat_cfg = StrategyConfig(name="risk_aware_etf_rotation_v1", version="v1")
            db.add(strat_cfg)
            db.flush()
        btc = BacktestConfig(
            strategy_config_id=strat_cfg.id,
            start_date=date.today().replace(year=date.today().year - 1),
            end_date=date.today(),
            initial_capital=100000.0,
        )
        db.add(btc)
        db.flush()
        req.backtest_config_id = btc.id

    grader = AuditGrader(db)
    audit = grader.run_audit(req.strategy_config_id or strat_cfg.id, req.backtest_config_id)
    db.commit()
    return {...}
```

- Add imports: `from app.backtest.models import BacktestConfig`, `from app.strategy.models import StrategyConfig`, `from datetime import date`

**Verify:**
```bash
curl -X POST localhost:8001/audit/run -H "Content-Type: application/json" -d '{"strategy_config_id":1,"backtest_config_id":1}'
# Should return 200 with grade
```

---

## Task 4: Fix frontend pages — proper empty/error/loading states

**Files:**
- Modify: `frontend/src/pages/Signals.tsx` — fix signal display shape
- Modify: `frontend/src/pages/Backtest.tsx` — add "run backtest" button + empty state
- Modify: `frontend/src/pages/Audit.tsx` — add "run audit" button + empty state
- Modify: `frontend/src/pages/Risk.tsx` — handle empty rules

For each page, ensure three states render correctly:
1. **Loading**: Skeleton/spinner while fetching
2. **Error**: Red banner with error message + retry button
3. **Empty**: Friendly message with action button ("No signals yet — run strategy first")
4. **Populated**: Data table/chart

---

## Task 5: Add backend tests

**Files:**
- Create: `backend/tests/test_api_endpoints.py`

Basic smoke tests for all endpoints:

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_instruments():
    response = client.get("/data/instruments")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_risk_state():
    response = client.get("/risk/state")
    assert response.status_code == 200
    assert "state" in response.json()

def test_features_definitions():
    response = client.get("/features/definitions")
    assert response.status_code == 200
    assert len(response.json()) == 17
```

**Verify:**
```bash
pytest backend/tests/test_api_endpoints.py -v
```

---

## Task 6: Deploy, full E2E test, and commit

- Deploy all fixes to server
- Run full test suite through Vite proxy
- Verify all 10 endpoints pass
- Open browser and verify all pages load
- Commit and push to main
