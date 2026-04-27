# Reproducibility Guide

Every backtest and audit run stores immutable configuration for reproducibility.

## Config Hashes

- **Feature config hash:** SHA-256 of all FeatureDefinition (name, lookback_days, parameters)
- **Strategy config hash:** SHA-256 of strategy name, version, parameters, feature weights
- **Backtest config hash:** SHA-256 of date range, initial capital, cost model, strategy config ID

## Backtest Reproducibility

Each BacktestRun stores `config_hash`. To reproduce:
1. Note the `config_hash` from the run
2. Use the same strategy config and data version
3. Re-run with identical parameters
4. Compare resulting metrics — they must match exactly

## Data Versioning

- All DailyBar records include `data_source` and `fetched_at` timestamps
- Raw data is append-only — no deletions
- Data quality reports track any issues detected

## Exact Commands to Reproduce Figures

```bash
# Equity curve
curl localhost:8000/backtest/results/1 | jq '.equity_curve'

# Performance metrics
curl localhost:8000/backtest/results/1 | jq '.metrics'

# Audit report
curl localhost:8000/audit/report/1 | jq .
```

## Figure Generation

```python
from app.reports.figures import equity_curve_figure, drawdown_figure
from app.reports.tables import metrics_to_markdown

# Generate from backtest results
results = requests.get("http://localhost:8000/backtest/results/1").json()
equity_curve_figure(results["equity_curve"], output_path="output/equity.png")
drawdown_figure(results["equity_curve"], output_path="output/drawdown.png")
print(metrics_to_markdown(results["metrics"]))
```
