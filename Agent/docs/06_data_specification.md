# 06 — Data Specification

## Primary data sources

### AKShare

Primary source for A-share ETF and China market data. Use it because it is open-source, Python-native, and broadly covers Chinese financial data.

### Tushare

Optional enhanced source if token and access permissions are available. Use for stability checks and potentially richer metadata.

### efinance

Optional backup or real-time snapshot source. Treat as best-effort because it is a personal open-source library and its own documentation states it is for learning and communication use.

## Data source policy

- Store source name and fetch timestamp for every record.
- Do not silently mix adjusted and unadjusted prices.
- Keep raw data and cleaned data separate.
- Add data-quality flags rather than silently deleting bad records.
- Do not assume a data source is production-grade unless verified.

## Instrument master fields

| Field | Type | Description |
|---|---|---|
| symbol | string | Internal normalized symbol. |
| exchange | string | SSE/SZSE/other. |
| name | string | ETF name. |
| asset_class | string | equity/bond/gold/money-market/other. |
| category | string | broad/sector/theme/defensive/style. |
| benchmark_index | string | Tracking index if available. |
| inception_date | date | Fund listing/inception date if available. |
| active | bool | Whether eligible for current universe. |
| min_data_start | date | Earliest reliable data date. |

## Daily bar fields

| Field | Type |
|---|---|
| symbol | string |
| trade_date | date |
| open | decimal |
| high | decimal |
| low | decimal |
| close | decimal |
| volume | decimal |
| amount | decimal |
| adj_factor | decimal/null |
| source | string |
| fetched_at | timestamp |
| quality_flags | json |

## Realtime snapshot fields

MVP can implement this as optional:

| Field | Type |
|---|---|
| symbol | string |
| snapshot_time | timestamp |
| last_price | decimal |
| bid | decimal/null |
| ask | decimal/null |
| volume | decimal/null |
| amount | decimal/null |
| premium_discount_proxy | decimal/null |
| source | string |

## Data quality checks

- Missing trading days.
- Duplicate bars.
- Non-positive prices.
- High < low inconsistencies.
- Open/close outside high-low range.
- Zero or near-zero volume.
- Extreme daily return beyond threshold.
- Stale price sequences.
- Source mismatch between AKShare and Tushare/efinance if multiple sources exist.

## Survivorship bias control

The MVP should record whether an ETF existed at each historical date. If full historical constituent availability is unavailable, the report must state the limitation. The audit module should include a warning when the ETF universe is based on current listed funds only.

## Data leakage control

Every feature computation must include:

- `data_as_of`: last date included in feature calculation.
- `decision_time`: time at which signal is generated.
- `execution_time`: assumed trade execution time.

Features used for a weekly rebalance must only use data available at `decision_time`.

## Cache policy

- Raw data should be append-only.
- Cleaned bars can be recomputed.
- Feature values can be cached by `(feature_name, symbol, as_of_date, config_hash)`.
- Backtest results should be immutable by config hash.

## Configuration files

Suggested files:

- `config/universe/a_share_etf_core.yaml`
- `config/data_sources.yaml`
- `config/market_calendar.yaml`
- `config/risk_profiles.yaml`
