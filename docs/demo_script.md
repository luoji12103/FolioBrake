# Retail ETF Guardian — Demo Script

## Prerequisites

- Linux server with Docker and Docker Compose
- Git

## Step 1: Clone and Start

```bash
git clone https://github.com/luoji12103/FolioBrake.git
cd FolioBrake
docker compose -f ops/docker-compose.yml up --build -d
curl localhost:8000/health  # {"status":"ok","version":"0.1.0"}
```

## Step 2: Sync ETF Data

```bash
curl -X POST localhost:8000/data/sync \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["510050","510300","510500","159919","159915"], "start_date": "20240101", "end_date": "20260331"}'

curl localhost:8000/data/instruments  # Verify instruments loaded
```

## Step 3: Seed Features

```bash
cd backend && python scripts/seed_features.py
```

## Step 4: Compute Features

```bash
curl -X POST localhost:8000/features/compute \
  -H "Content-Type: application/json" \
  -d '{"instrument_id": 1, "as_of_date": "2026-03-31"}'
```

## Step 5: Run Strategy

```bash
curl -X POST localhost:8000/strategy/run \
  -H "Content-Type: application/json" \
  -d '{"as_of_date": "2026-03-31"}'

curl localhost:8000/strategy/signals   # View signals
curl localhost:8000/strategy/portfolio  # View target portfolio
```

## Step 6: Run Backtest

```bash
curl -X POST localhost:8000/backtest/run \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2025-01-01", "end_date": "2026-03-31", "initial_capital": 100000}'

curl localhost:8000/backtest/results/1  # View results
```

## Step 7: Run Audit

```bash
curl -X POST localhost:8000/audit/run \
  -H "Content-Type: application/json" \
  -d '{"strategy_config_id": 1, "backtest_config_id": 1}'

curl localhost:8000/audit/report/1  # View GREEN/YELLOW/RED grade
```

## Step 8: Paper Portfolio

```bash
curl -X POST localhost:8000/paper/portfolio \
  -H "Content-Type: application/json" \
  -d '{"name": "demo", "initial_capital": 100000}'

curl localhost:8000/paper/pnl/1  # View P&L
```

## Step 9: Check Risk Overlay

```bash
curl localhost:8000/risk/state     # Current risk state
curl localhost:8000/risk/rules     # Triggered rules
curl localhost:8000/risk/overlay   # Latest overlay decision
```

## Step 10: Frontend

```bash
cd frontend
npm install --cache /tmp/npm-cache
npm run dev
# Open http://localhost:1420
```
