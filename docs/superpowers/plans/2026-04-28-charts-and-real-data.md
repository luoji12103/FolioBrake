# Charts Integration & Real Data Source Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace synthetic test data with real ETF historical prices via efinance, integrate Recharts visualizations into Backtest and Signals pages.

**Architecture:** Add EfinanceAdapter as second data source beside AKShare, sync real ~5000-row OHLCV bars for 5 ETFs into Postgres, then wire existing EquityChart/DrawdownChart/WeightBarChart components into Backtest and Signals pages with real data.

**Tech Stack:** Python efinance, Recharts, React + TypeScript

---

## Task 1: Add efinance adapter and register as fallback data source

**Files:**
- Modify: `backend/app/data/adapter.py`
- Create: `backend/app/data/efinance_adapter.py`

- [ ] **Step 1: Create EfinanceAdapter**

```python
# backend/app/data/efinance_adapter.py
import logging
import efinance as ef
import pandas as pd

logger = logging.getLogger(__name__)


class EfinanceAdapter:
    """efinance-based ETF data adapter. Works independent of AKShare."""

    COLUMN_MAP = {
        "日期": "trade_date",
        "单位净值": "close",
        "累计净值": "adj_close",
        "涨跌幅": "change_pct",
        "成交量": "volume",
        "成交额": "amount",
    }

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        return str(symbol).strip().zfill(6)

    def fetch_etf_daily(self, symbol: str, start_date: str = "20100101",
                        end_date: str = "20260427") -> list[dict]:
        symbol = self.normalize_symbol(symbol)
        try:
            df: pd.DataFrame = ef.fund.get_quote_history(symbol)
            if df.empty:
                logger.warning("efinance returned empty data for %s", symbol)
                return []

            df = df.rename(columns=self.COLUMN_MAP)
            # Filter date range
            df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.strftime("%Y-%m-%d")
            df = df[(df["trade_date"] >= _reformat_date(start_date)) &
                    (df["trade_date"] <= _reformat_date(end_date))]

            records = []
            for _, row in df.iterrows():
                rec = {"trade_date": row["trade_date"], "close": float(row.get("close", 0) or 0)}
                if "volume" in row and pd.notna(row["volume"]):
                    rec["volume"] = float(row["volume"])
                else:
                    rec["volume"] = 0.0
                if "amount" in row and pd.notna(row["amount"]):
                    rec["amount"] = float(row["amount"])
                else:
                    rec["amount"] = 0.0
                if "adj_close" in row and pd.notna(row["adj_close"]):
                    rec["adj_close"] = float(row["adj_close"])
                rec["open"] = rec["close"]
                rec["high"] = rec["close"]
                rec["low"] = rec["close"]
                records.append(rec)
            logger.info("efinance: %d rows for %s", len(records), symbol)
            return records
        except Exception:
            logger.exception("efinance call failed for symbol=%s", symbol)
            return []


def _reformat_date(d: str) -> str:
    """Convert YYYYMMDD → YYYY-MM-DD."""
    if len(d) == 8:
        return f"{d[:4]}-{d[4:6]}-{d[6:8]}"
    return d
```

- [ ] **Step 2: Modify DataSyncService to try efinance as fallback**

In `backend/app/data/sync.py`, in `sync_daily_bars`, if AKShare returns 0 bars, try efinance:

```python
# After existing AKShare adapter fetch:
records = self.adapter.fetch_etf_daily(inst.symbol, start, end)

# Add fallback:
if not records:
    from app.data.efinance_adapter import EfinanceAdapter
    ef_adapter = EfinanceAdapter()
    records = ef_adapter.fetch_etf_daily(inst.symbol, start, end)
    if records:
        logger.info("Falling back to efinance for %s", inst.symbol)
```

- [ ] **Step 3: Deploy and sync real data**

```bash
scp ... ClawCloud-JP-8C32G-320G-1T1G-LXC:/tmp/FolioBrake/backend/app/data/
docker compose ... up --build -d --force-recreate api-server
curl -X POST localhost:8001/api/data/sync -H "Content-Type: application/json" \
  -d '{"symbols":["510050","510300","510500","159919","159915"],"start_date":"20220101","end_date":"20260427"}'
# Expected: 5000+ bars per symbol
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/data/efinance_adapter.py backend/app/data/sync.py
git commit -m "feat: add efinance adapter as fallback data source for real ETF prices"
```

---

## Task 2: Integrate EquityChart into Backtest page

**Files:**
- Modify: `frontend/src/pages/Backtest.tsx`

- [ ] **Step 1: Add EquityChart import and render**

```typescript
import { EquityChart } from "../components/Charts";
```

After the metrics card grid, add the chart:

```tsx
{results?.equity_curve && results.equity_curve.length > 0 && (
  <div className="card" style={{marginTop: 16}}>
    <h3>Equity Curve</h3>
    <EquityChart data={results.equity_curve.map((p: any) => ({
      date: p.date,
      total_value: p.total_value,
    }))} />
  </div>
)}
```

- [ ] **Step 2: Add DrawdownChart below equity**

```tsx
{results?.equity_curve && results.equity_curve.length > 0 && (() => {
  const ddData = results.equity_curve.map((p: any) => {
    const peak = Math.max(...results.equity_curve
      .slice(0, results.equity_curve.indexOf(p) + 1)
      .map((x: any) => x.total_value));
    return { date: p.date, drawdown: (p.total_value - peak) / peak * 100 };
  });
  return (
    <div className="card" style={{marginTop: 16}}>
      <h3>Drawdown</h3>
      <DrawdownChart data={ddData} />
    </div>
  );
})()}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Backtest.tsx
git commit -m "feat: integrate EquityChart and DrawdownChart into Backtest page"
```

---

## Task 3: Integrate WeightBarChart into Signals page

**Files:**
- Modify: `frontend/src/pages/Signals.tsx`

- [ ] **Step 1: Add WeightBarChart**

```typescript
import { WeightBarChart } from "../components/Charts";
```

After the signals table, add:

```tsx
{portfolio && portfolio.length > 0 && (
  <div className="card" style={{marginTop: 16}}>
    <h3>Target Weights</h3>
    <WeightBarChart data={portfolio.map((p: any) => ({
      symbol: p.symbol,
      target_weight: p.target_weight * 100,
    }))} />
  </div>
)}
```

Need to fetch portfolio data: add `usePortfolio` import and call at top of SignalsTable or parent.

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/Signals.tsx
git commit -m "feat: integrate WeightBarChart into Signals page"
```

---

## Task 4: Rebuild, run full pipeline, verify

- [ ] **Step 1: Sync real data on server**

```bash
# SSH to server
cd /tmp/FolioBrake
docker compose ... up --build -d --force-recreate api-server
curl -X POST localhost:8001/api/data/sync \
  -H "Content-Type: application/json" \
  -d '{"symbols":["510050","510300","510500","159919","159915"],"start_date":"20220101","end_date":"20260427"}'
# Verify: >5000 bars per ETF
```

- [ ] **Step 2: Run full pipeline**

```bash
# Compute features
curl -X POST localhost:8001/api/features/compute -H "Content-Type: application/json" \
  -d '{"instrument_id":7,"as_of_date":"2026-04-25"}'
# Run strategy
curl -X POST localhost:8001/api/strategy/run -H "Content-Type: application/json" \
  -d '{"as_of_date":"2026-04-25"}'
# Run backtest
curl -X POST localhost:8001/api/backtest/run -H "Content-Type: application/json" \
  -d '{"start_date":"2022-01-01","end_date":"2026-04-25","initial_capital":100000}'
# Run audit
curl -X POST localhost:8001/api/audit/run -H "Content-Type: application/json" \
  -d '{"strategy_config_id":1,"backtest_config_id":1}'
```

- [ ] **Step 3: Verify frontend**

Open `http://localhost:1420/backtest` → run backtest → verify equity curve chart renders
Open `http://localhost:1420/signals` → verify weight bar chart renders

- [ ] **Step 4: TypeScript check and build**

```bash
cd frontend && npx tsc --noEmit && npm run build
```

- [ ] **Step 5: Commit and push**

```bash
git add -A && git commit -m "feat: real data sync via efinance, charts integrated"
git push origin main
```
