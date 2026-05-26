# FolioBrake Architecture

## Overview
FolioBrake is a risk-aware ETF trading decision system for A-share ETFs.

## Components
- **Backend**: FastAPI + SQLAlchemy + PostgreSQL + Redis
- **Frontend**: React + TypeScript + Vite
- **Workers**: Celery for async tasks
- **Monitoring**: Prometheus + Grafana

## Data Flow
1. Data ingestion from AKShare/eFinance
2. Feature computation (17 indicators)
3. Strategy scoring and ranking
4. Risk assessment
5. Portfolio construction
6. Backtesting and audit
7. Paper trading

## API Structure
- `/api/data` - Data management
- `/api/features` - Feature computation
- `/api/strategy` - Strategy execution
- `/api/risk` - Risk assessment
- `/api/backtest` - Backtesting
- `/api/audit` - Audit
- `/api/paper` - Paper trading
- `/api/analysis` - Data analysis
- `/api/ml` - Machine learning
- `/api/auth` - Authentication
