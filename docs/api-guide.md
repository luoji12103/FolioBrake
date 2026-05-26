# FolioBrake API Guide

## Base URL
```
http://localhost:8000/api
```

## Authentication
Currently no authentication required.

## Endpoints

### Health
- `GET /health` - Health check

### Data
- `GET /data/instruments` - List instruments
- `GET /data/bars/{symbol}` - Get daily bars
- `GET /data/quality/{symbol}` - Data quality check

### Strategy
- `GET /strategy/signals` - Get signals
- `GET /strategy/portfolio` - Get portfolio

### Risk
- `GET /risk/state` - Risk state
- `GET /risk/alerts` - Risk alerts

### Analysis
- `GET /analysis/drawdown/{symbol}` - Drawdown analysis
- `GET /analysis/var/{symbol}` - VaR analysis
