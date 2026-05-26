# API Reference

## Endpoints

### Data
- `GET /api/data/instruments` - List all instruments
- `GET /api/data/bars/{symbol}` - Get daily bars
- `GET /api/data/quality/{symbol}` - Data quality check
- `GET /api/data/health` - Data source health
- `POST /api/data/sync` - Sync data
- `GET /api/data/export/{symbol}` - Export data

### Features
- `GET /api/features/definitions` - List feature definitions
- `POST /api/features/compute` - Compute features
- `GET /api/features/values` - Get feature values

### Strategy
- `POST /api/strategy/run` - Run strategy
- `GET /api/strategy/signals` - Get signals
- `GET /api/strategy/portfolio` - Get portfolio
- `GET /api/strategy/configs` - List configs

### Risk
- `GET /api/risk/state` - Risk state
- `GET /api/risk/alerts` - Risk alerts
- `GET /api/risk/rules` - Risk rules
- `GET /api/risk/overlay` - Risk overlay

### Backtest
- `POST /api/backtest/run` - Run backtest
- `GET /api/backtest/results/{id}` - Get results
- `GET /api/backtest/status/{id}` - Get status

### Audit
- `POST /api/audit/run` - Run audit
- `GET /api/audit/report/{id}` - Get report

### Paper Trading
- `POST /api/paper/portfolio` - Create portfolio
- `GET /api/paper/portfolios` - List portfolios
- `GET /api/paper/pnl/{id}` - Get PnL
- `GET /api/paper/holdings/{id}` - Get holdings
- `POST /api/paper/import-holdings` - Import holdings

### Analysis
- `GET /api/analysis/drawdown/{symbol}` - Drawdown analysis
- `GET /api/analysis/var/{symbol}` - VaR analysis
- `GET /api/analysis/correlation` - Correlation matrix
