# 10 — Database Schema

This is a conceptual schema for PostgreSQL. Claude Code / Codex can convert it into SQLAlchemy models and Alembic migrations.

## instruments

| Column | Type |
|---|---|
| id | uuid pk |
| symbol | text unique |
| exchange | text |
| name | text |
| asset_class | text |
| category | text |
| benchmark_index | text null |
| inception_date | date null |
| active | bool |
| metadata | jsonb |
| created_at | timestamptz |
| updated_at | timestamptz |

## daily_bars_raw

| Column | Type |
|---|---|
| id | uuid pk |
| symbol | text |
| trade_date | date |
| open | numeric |
| high | numeric |
| low | numeric |
| close | numeric |
| volume | numeric |
| amount | numeric |
| adj_factor | numeric null |
| source | text |
| fetched_at | timestamptz |
| payload | jsonb |

Unique index: `(symbol, trade_date, source)`.

## daily_bars_clean

| Column | Type |
|---|---|
| id | uuid pk |
| symbol | text |
| trade_date | date |
| open | numeric |
| high | numeric |
| low | numeric |
| close | numeric |
| adjusted_close | numeric null |
| volume | numeric |
| amount | numeric |
| quality_flags | jsonb |
| data_version | text |

Unique index: `(symbol, trade_date, data_version)`.

## feature_values

| Column | Type |
|---|---|
| id | uuid pk |
| symbol | text |
| feature_name | text |
| as_of_date | date |
| value | numeric |
| config_hash | text |
| data_version | text |
| created_at | timestamptz |

Unique index: `(symbol, feature_name, as_of_date, config_hash, data_version)`.

## strategy_runs

| Column | Type |
|---|---|
| id | uuid pk |
| strategy_name | text |
| risk_profile | text |
| as_of_date | date |
| config | jsonb |
| config_hash | text |
| status | text |
| created_at | timestamptz |
| completed_at | timestamptz null |

## signals

| Column | Type |
|---|---|
| id | uuid pk |
| strategy_run_id | uuid fk |
| symbol | text |
| score | numeric |
| raw_weight | numeric |
| target_weight | numeric |
| explanation | jsonb |

## risk_overlay_results

| Column | Type |
|---|---|
| id | uuid pk |
| strategy_run_id | uuid fk |
| portfolio_id | uuid null |
| as_of_date | date |
| risk_state | text |
| decision | text |
| original_targets | jsonb |
| final_targets | jsonb |
| rule_results | jsonb |
| explanation | text |

## backtest_runs

| Column | Type |
|---|---|
| id | uuid pk |
| strategy_name | text |
| config | jsonb |
| config_hash | text |
| start_date | date |
| end_date | date |
| initial_cash | numeric |
| status | text |
| created_at | timestamptz |
| completed_at | timestamptz null |

## portfolio_snapshots

| Column | Type |
|---|---|
| id | uuid pk |
| backtest_id | uuid fk |
| trade_date | date |
| total_value | numeric |
| cash | numeric |
| positions | jsonb |
| weights | jsonb |
| drawdown | numeric |

## simulated_orders

| Column | Type |
|---|---|
| id | uuid pk |
| backtest_id | uuid fk null |
| paper_portfolio_id | uuid null |
| symbol | text |
| side | text |
| quantity | numeric |
| order_price | numeric |
| filled_price | numeric null |
| cost | numeric |
| slippage | numeric |
| status | text |
| created_at | timestamptz |
| filled_at | timestamptz null |
| explanation | jsonb |

## performance_metrics

| Column | Type |
|---|---|
| id | uuid pk |
| backtest_id | uuid fk |
| metric_name | text |
| metric_value | numeric |
| metadata | jsonb |

## audit_runs

| Column | Type |
|---|---|
| id | uuid pk |
| backtest_id | uuid fk |
| audit_profile | text |
| audit_grade | text |
| audit_score | numeric |
| status | text |
| created_at | timestamptz |
| completed_at | timestamptz null |

## audit_check_results

| Column | Type |
|---|---|
| id | uuid pk |
| audit_id | uuid fk |
| check_name | text |
| status | text |
| score | numeric |
| severity | text |
| details | jsonb |
| explanation | text |

## paper_portfolios

| Column | Type |
|---|---|
| id | uuid pk |
| name | text |
| initial_cash | numeric |
| current_cash | numeric |
| risk_profile | text |
| created_at | timestamptz |

## paper_positions

| Column | Type |
|---|---|
| id | uuid pk |
| portfolio_id | uuid fk |
| symbol | text |
| quantity | numeric |
| avg_cost | numeric |
| updated_at | timestamptz |
