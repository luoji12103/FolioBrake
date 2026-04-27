# 09 — API Contracts

## API style

Use REST for MVP. Add WebSocket only for progress updates and optional realtime risk monitoring.

Base path: `/api/v1`

## Health

### `GET /health`

Response:

```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

## Universe

### `GET /universe`

Returns configured ETF universe.

### `POST /universe/import`

Imports a YAML/CSV universe.

### `GET /instruments/{symbol}`

Returns instrument metadata.

## Data

### `POST /data/sync`

Starts data sync job.

Request:

```json
{
  "source": "akshare",
  "symbols": ["510300.SH"],
  "start_date": "2018-01-01",
  "end_date": "2026-04-27"
}
```

Response:

```json
{
  "job_id": "uuid",
  "status": "queued"
}
```

### `GET /data/jobs/{job_id}`

Returns job status.

### `GET /data/bars/{symbol}`

Query params:

- `start_date`
- `end_date`
- `adjusted=true|false`

## Strategy

### `GET /strategies`

Returns available strategies.

### `POST /strategies/run`

Runs latest signal generation.

Request:

```json
{
  "strategy_name": "risk_aware_etf_rotation_v1",
  "risk_profile": "balanced",
  "as_of_date": "2026-04-24"
}
```

Response:

```json
{
  "run_id": "uuid",
  "status": "queued"
}
```

### `GET /strategies/runs/{run_id}`

Returns signal run result including scores and explanations.

## Risk overlay

### `POST /risk/evaluate`

Request:

```json
{
  "strategy_run_id": "uuid",
  "portfolio_id": "default",
  "as_of_date": "2026-04-24"
}
```

Response:

```json
{
  "risk_state": "CAUTION",
  "decision": "REDUCE",
  "reasons": ["volatility_spike", "market_trend_negative"]
}
```

## Backtest

### `POST /backtests`

Request:

```json
{
  "strategy_name": "risk_aware_etf_rotation_v1",
  "risk_profile": "balanced",
  "universe_id": "a_share_etf_core",
  "start_date": "2018-01-01",
  "end_date": "2026-04-24",
  "initial_cash": 100000,
  "cost_bps": 5,
  "slippage_bps": 5,
  "rebalance_frequency": "W"
}
```

Response:

```json
{
  "backtest_id": "uuid",
  "status": "queued"
}
```

### `GET /backtests/{backtest_id}`

Returns performance summary, equity curve, trades, and logs.

## Audit

### `POST /audits`

Request:

```json
{
  "backtest_id": "uuid",
  "audit_profile": "standard"
}
```

Response:

```json
{
  "audit_id": "uuid",
  "status": "queued"
}
```

### `GET /audits/{audit_id}`

Returns audit grade and check results.

## Paper/simulated trading

### `POST /paper/portfolios`

Creates a simulated portfolio.

### `POST /paper/portfolios/{portfolio_id}/apply-signal`

Applies an approved strategy signal to simulated portfolio ledger.

Should reject if audit is not GREEN unless user explicitly overrides in dev mode.

## Reports

### `GET /reports/backtest/{backtest_id}`

Returns JSON report data.

### `GET /reports/audit/{audit_id}`

Returns JSON audit report data.

## Error format

```json
{
  "error": {
    "code": "DATA_NOT_AVAILABLE",
    "message": "No cleaned bars found for 510300.SH in requested date range.",
    "details": {}
  }
}
```
