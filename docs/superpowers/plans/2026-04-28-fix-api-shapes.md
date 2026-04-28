# Frontend/Backend Integration Fix Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all "detail: Not Found" errors and 500 errors across frontend pages, match API response shapes to component expectations, seed required data.

**Architecture:** Root causes: (1) Pydantic response model mismatches with SQLAlchemy types, (2) empty/error states not handled gracefully in frontend pages, (3) Feature definitions and backtest/audit runs not seeded.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.x, React + TypeScript, Vite.

---

## Diagnosed Issues

| # | Endpoint / Page | Error | Root Cause |
|---|----------------|-------|------------|
| 1 | `GET /data/bars/{symbol}` | 500 | `BarOut.trade_date: str` vs SQLAlchemy `date` object |
| 2 | `GET /data/quality/{symbol}` | `{"detail":"..."}` | Error dict exposes FastAPI detail format to frontend |
| 3 | `GET /features/definitions` | `[]` | Feature definitions not seeded |
| 4 | `GET /backtest/status/1` | `"Run not found"` | No backtest runs executed |
| 5 | `GET /audit/status/1` | `"Audit run not found"` | No audit runs executed |
| 6 | Backtest page | Blank | Calls `/backtest/results/{runId}` but no runId available |
| 7 | Audit page | Blank | Calls `/audit/report/{runId}` but no runId available |
| 8 | Signals page | `detail: Not Found` | `useSignals` fetches correctly but response shape may misrender |
| 9 | `GET /risk/rules` | `[]` | No rules evaluated yet |

---

## Branch: `fix-api-shapes`

### Task 1: Fix BarOut Pydantic serialization

**Files:**
- Modify: `backend/app/api/data.py:52-61`

- [ ] **Step 1: Fix trade_date type**

```python
from datetime import date as date_type
from pydantic import field_serializer

class BarOut(BaseModel):
    trade_date: date_type
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float
    adj_close: Optional[float] = None

    model_config = {"from_attributes": True}

    @field_serializer("trade_date")
    def serialize_trade_date(self, v: date_type) -> str:
        return v.isoformat()
```

- [ ] **Step 2: Verify**

```bash
curl -s localhost:8001/data/bars/510050 | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{len(d)} bars')"
# Expected: "301 bars"
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/data.py
git commit -m "fix: BarOut trade_date serialization — use date type with field_serializer"
```

### Task 2: Fix quality endpoint response

**Files:**
- Modify: `backend/app/api/data.py:155-175`

- [ ] **Step 1: Return proper error instead of raw detail dict**

```python
@router.get("/quality/{symbol}", response_model=QualityReportOut)
def get_quality(symbol: str, db: Session = Depends(get_db)):
    adapter = AKShareAdapter()
    normalised = adapter.normalize_symbol(symbol)

    inst = db.execute(select(Instrument).where(Instrument.symbol == normalised)).scalar_one_or_none()
    if not inst:
        raise HTTPException(status_code=404, detail=f"Instrument not found: {symbol}")

    report = db.execute(
        select(DataQualityReport)
        .where(DataQualityReport.instrument_id == inst.id)
        .order_by(DataQualityReport.check_date.desc())
        .limit(1)
    ).scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail=f"No quality report found for {symbol}")

    return report
```

- [ ] **Step 2: Verify**

```bash
curl -s localhost:8001/data/quality/510050
# Expected: 404 with proper detail, not 500
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/data.py
git commit -m "fix: quality endpoint returns proper HTTPException instead of raw dict"
```

### Task 3: Seed feature definitions automatically

**Files:**
- Create: `backend/app/api/features.py` (modify)

- [ ] **Step 1: Add seed endpoint**

```python
@router.post("/seed")
def seed_features(db: Session = Depends(get_db)):
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
    count = 0
    for name, cat, lookback, params in FEATURES:
        existing = db.execute(
            select(FeatureDefinition).where(FeatureDefinition.name == name)
        ).scalar_one_or_none()
        if not existing:
            db.add(FeatureDefinition(name=name, category=cat, lookback_days=lookback, parameters=params))
            count += 1
    db.commit()
    return {"seeded": count, "total": len(FEATURES)}
```

- [ ] **Step 2: Verify**

```bash
curl -s -X POST localhost:8001/features/seed && curl -s localhost:8001/features/definitions | python3 -c "import sys,json; print(len(json.load(sys.stdin)))"
# Expected: seeded 17, then 17 definitions
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/features.py
git commit -m "feat: add POST /features/seed endpoint"
```

### Task 4: Add auto-seed on startup

**Files:**
- Modify: `backend/app/main.py`

- [ ] **Step 1: Add startup event to seed features**

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Seed feature definitions on startup
    from app.db.base import SessionLocal
    from app.features.models import FeatureDefinition
    from sqlalchemy import select
    db = SessionLocal()
    try:
        existing = db.execute(select(FeatureDefinition).limit(1)).scalar_one_or_none()
        if not existing:
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
            for name, cat, lookback, params in FEATURES:
                db.add(FeatureDefinition(name=name, category=cat, lookback_days=lookback, parameters=params))
            db.commit()
    finally:
        db.close()
    yield

app = FastAPI(title="Retail ETF Guardian API", version="0.1.0", lifespan=lifespan)
```

- [ ] **Step 2: Verify after rebuild**

```bash
curl -s localhost:8001/features/definitions | python3 -c "import sys,json; print(len(json.load(sys.stdin)))"
# Expected: 17
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/main.py
git commit -m "feat: auto-seed feature definitions on app startup"
```

### Task 5: Fix frontend pages to handle empty/error states gracefully

**Files:**
- Modify: `frontend/src/pages/Signals.tsx` — check signal response shape
- Modify: `frontend/src/pages/Backtest.tsx` — handle "no run yet" state
- Modify: `frontend/src/pages/Audit.tsx` — handle "no audit yet" state
- Modify: `frontend/src/pages/Risk.tsx` — handle empty rules list

- [ ] **Step 1: Fix Signals page — response shape from API is `{instrument_id, symbol, score, rank, reason}`, not the old shapes**

Check current `useSignals` usage and ensure the component renders actual fields.

- [ ] **Step 2: Fix Backtest page — add state for "no runs yet"**

Currently the page tries `/backtest/results/1` which returns `{"error":"..."}`. Fix:
- Add a "Run Backtest" button that POSTs `/backtest/run`
- Show loading state during run
- Show results only after successful run
- Handle "no runs exist" as initial empty state

```typescript
function Backtest() {
  const [runId, setRunId] = useState<number | null>(null);
  // ... run backtest form, then navigate to results
  return (
    <div className="page">
      <h2>Backtest</h2>
      {/* Config form */}
      <RunBacktestForm onComplete={setRunId} />
      {/* Results */}
      {runId && <BacktestResults runId={runId} />}
      {!runId && <div className="state-banner state-empty">Run a backtest to see results.</div>}
    </div>
  );
}
```

- [ ] **Step 3: Fix Audit page — same pattern as Backtest**

- [ ] **Step 4: Fix Risk page — handle empty rules gracefully**

Rules endpoint returns `[]` when no rules evaluated. Show "No rules triggered today" instead of error.

- [ ] **Step 5: Verify all pages render without errors**

```bash
curl -s localhost:1420/health  # Dashboard works
curl -s localhost:1420/data/instruments  # Universe works
curl -s localhost:1420/strategy/signals  # Signals works
curl -s localhost:1420/risk/state  # Risk works
curl -s localhost:1420/paper/pnl/1  # Paper works
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/
git commit -m "fix: handle empty/error states in Signals, Backtest, Audit, Risk pages"
```

### Task 6: Deploy and integration test

- [ ] **Step 1: Deploy all backend fixes to server**

```bash
scp ... ClawCloud-JP-8C32G-320G-1T1G-LXC:/tmp/FolioBrake/backend/app/
docker compose -f ops/docker-compose.yml -p foliobrake-test up --build -d --force-recreate api-server
```

- [ ] **Step 2: Run full API test**

```bash
curl -s localhost:8001/health
curl -s localhost:8001/data/bars/510050 | python3 -c "import sys,json; print(f'{len(json.load(sys.stdin))} bars')"
curl -s localhost:8001/features/definitions | python3 -c "import sys,json; print(f'{len(json.load(sys.stdin))} defs')"
curl -s localhost:8001/strategy/run -X POST -H "Content-Type: application/json" -d '{"as_of_date":"2025-10-28"}'
curl -s localhost:8001/backtest/run -X POST -H "Content-Type: application/json" -d '{"start_date":"2025-01-01","end_date":"2025-10-28","initial_capital":100000}'
curl -s localhost:8001/audit/run -X POST -H "Content-Type: application/json" -d '{"strategy_config_id":1,"backtest_config_id":1}'
```

- [ ] **Step 3: Verify frontend builds and all pages load**

```bash
npx tsc --noEmit && npm run build
# Open http://localhost:1420 and navigate all pages
```

- [ ] **Step 4: Commit and push**

```bash
git push origin fix-api-shapes
# Merge to main
```
