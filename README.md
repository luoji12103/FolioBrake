<div align="center">

# 🛡️ FolioBrake

**Risk-Aware ETF Trading Decision System for A-Share Markets**

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/luoji12103/FolioBrake/releases/tag/v1.0.0)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/react-18-61DAFB.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/typescript-5.0-3178C6.svg)](https://www.typescriptlang.org/)
[![Docker](https://img.shields.io/badge/docker-compose-2496ED.svg)](https://docs.docker.com/compose/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

*A comprehensive ETF trading system combining risk-aware rotation, backtest auditing, and paper trading for individual investors.*

[Features](#features) • [Quick Start](#quick-start) • [Architecture](#architecture) • [API](#api) • [Documentation](#documentation)

</div>

---

## 📋 Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [API Reference](#api-reference)
- [Frontend](#frontend)
- [Configuration](#configuration)
- [Development](#development)
- [Deployment](#deployment)
- [Testing](#testing)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

---

## ✨ Features

### 🎯 Core Trading System
- **Risk-Aware ETF Rotation** - Weekly portfolio allocation with drawdown, turnover, concentration, and volatility constraints
- **Backtest Engine** - Historical simulation with cost model (commission + slippage)
- **Audit Gatekeeper** - 7 validation checks before allowing paper trading
- **Paper Trading** - Simulated positions with P&L tracking

### 📊 Data & Analytics
- **17 Technical Indicators** - Momentum, volatility, trend, drawdown, liquidity
- **Real-time Risk Monitoring** - State machine (NORMAL → CAUTION → DEFENSIVE → HALT)
- **Signal History** - Track past signals and their performance
- **Portfolio Analytics** - Equity curve, drawdown, benchmark comparison

### 🔒 Security
- **JWT Authentication** - Secure API access
- **Rate Limiting** - Prevent abuse
- **Input Validation** - SQL injection protection
- **CORS & Security Headers** - XSS and CSRF protection
- **Audit Logging** - Track all user actions

### 🖥️ Frontend
- **8 Pages** - Dashboard, Universe, Signals, Risk, Backtest, Audit, Paper, Settings
- **Dark/Light Theme** - Toggle between themes
- **Responsive Design** - Works on desktop and mobile
- **Interactive Charts** - Zoom, pan, tooltips with Recharts
- **Data Export** - CSV/JSON export functionality

### 🏗️ Infrastructure
- **Docker Compose** - One-command deployment
- **PostgreSQL 16** - Primary database
- **Redis 7** - Caching and task queue
- **Prometheus** - Monitoring and metrics
- **Auto-backup** - Database backup scripts

---

## 🚀 Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/luoji12103/FolioBrake.git
cd FolioBrake

# Create environment file
cp ops/.env.example ops/.env
# Edit ops/.env with your settings

# Start all services
cd ops
docker compose up -d --build

# Verify health
curl http://localhost:8000/api/health
```

### Access

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:1420 |
| **API Docs** | http://localhost:8000/docs |
| **Prometheus** | http://localhost:18000 |

### Seed Demo Data

```bash
# Run the seed script to populate demo data
DATABASE_URL="postgresql+psycopg://guardian:guardian@localhost:5433/guardian" \
  python3 scripts/seed_demo_data.py
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Tauri Desktop GUI                        │
│                      (Frontend)                            │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP/WebSocket
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                 Docker Compose Stack                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   FastAPI     │  │  PostgreSQL  │  │    Redis     │     │
│  │   API Server  │  │     16      │  │      7       │     │
│  └──────┬───────┘  └──────────────┘  └──────────────┘     │
│         │                                                  │
│  ┌──────┴───────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Celery     │  │  Prometheus  │  │    Nginx     │     │
│  │   Workers    │  │  Monitoring  │  │   Reverse    │     │
│  └──────────────┘  └──────────────┘  │    Proxy     │     │
│                                       └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Backend** | Python 3.11+, FastAPI | API server |
| **Database** | PostgreSQL 16 | Data storage |
| **Cache** | Redis 7 | Caching, task queue |
| **Frontend** | React 18, TypeScript, Vite | User interface |
| **Charts** | Recharts | Data visualization |
| **Deployment** | Docker Compose | Container orchestration |
| **Monitoring** | Prometheus | Metrics collection |

---

## 📡 API Reference

### Core Endpoints

| Category | Endpoint | Method | Description |
|----------|----------|--------|-------------|
| **Health** | `/api/health` | GET | System health check |
| **Data** | `/api/data/instruments` | GET | List all ETF instruments |
| **Data** | `/api/data/bars/{symbol}` | GET | Get daily OHLCV bars |
| **Data** | `/api/data/quality/{symbol}` | GET | Data quality check |
| **Features** | `/api/features/definitions` | GET | List feature definitions |
| **Strategy** | `/api/strategy/run` | POST | Run trading strategy |
| **Strategy** | `/api/strategy/signals` | GET | Get trading signals |
| **Risk** | `/api/risk/state` | GET | Current risk state |
| **Risk** | `/api/risk/alerts` | GET | Risk alerts |
| **Backtest** | `/api/backtest/run` | POST | Run backtest |
| **Backtest** | `/api/backtest/results/{id}` | GET | Get backtest results |
| **Audit** | `/api/audit/run` | POST | Run audit |
| **Audit** | `/api/audit/report/{id}` | GET | Get audit report |
| **Paper** | `/api/paper/portfolio` | POST | Create paper portfolio |
| **Paper** | `/api/paper/pnl/{id}` | GET | Get P&L |
| **Analysis** | `/api/analysis/drawdown/{symbol}` | GET | Drawdown analysis |
| **Analysis** | `/api/analysis/var/{symbol}` | GET | Value at Risk |

### Authentication

```bash
# Login to get JWT token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# Use token in requests
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/data/instruments
```

---

## 🖥️ Frontend

### Pages

| Page | Route | Description |
|------|-------|-------------|
| **Dashboard** | `/` | Overview with risk state, signals, portfolio |
| **Universe** | `/universe` | Manage ETF watchlist |
| **Signals** | `/signals` | View trading signals, run strategy |
| **Risk** | `/risk` | Monitor risk state and alerts |
| **Backtest** | `/backtest` | Run and view backtests |
| **Audit** | `/audit` | Run and view audits |
| **Paper** | `/paper` | Paper trading portfolio |
| **Settings** | `/settings` | User preferences |

### Components

- **Charts** - Equity curve, drawdown, weight distribution
- **Data Tables** - Sortable, filterable, paginated
- **Toast Notifications** - Success/error feedback
- **Theme Toggle** - Dark/light mode
- **Keyboard Shortcuts** - Ctrl+K for search

---

## ⚙️ Configuration

### Environment Variables

```bash
# Application
APP_ENV=dev
SECRET_KEY=your-secret-key-here

# Database
POSTGRES_USER=guardian
POSTGRES_PASSWORD=your-password
POSTGRES_DB=guardian
DATABASE_URL=postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}

# Redis
REDIS_URL=redis://redis:6379/0

# Data
DATA_DIR=./data
TUSHARE_TOKEN=your-tushare-token
```

### Strategy Configuration

```json
{
  "name": "risk_aware_etf_rotation_v1",
  "version": "v1",
  "parameters": {
    "max_holdings": 5,
    "max_concentration": 0.30,
    "min_positions": 3,
    "max_turnover": 0.50
  }
}
```

---

## 💻 Development

### Local Setup

```bash
# Backend
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Project Structure

```
FolioBrake/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Core utilities
│   │   ├── db/           # Database models
│   │   ├── services/     # Business logic
│   │   ├── analysis/     # Data analysis
│   │   └── ml/           # Machine learning
│   └── tests/
├── frontend/
│   └── src/
│       ├── components/   # React components
│       ├── pages/        # Page components
│       ├── hooks/        # Custom hooks
│       └── api/          # API client
├── ops/
│   ├── docker-compose.yml
│   └── nginx/
└── docs/
```

---

## 🚢 Deployment

### Production

```bash
# Use production compose file
cd ops
cp .env.example .env
# Edit .env with production values

docker compose -f docker-compose.prod.yml up -d --build
```

### Health Checks

```bash
# Check all services
curl http://localhost:8000/api/health
curl http://localhost:1420
curl http://localhost:18000
```

### Backup

```bash
# Run backup script
bash ops/backup.sh
```

---

## 🧪 Testing

```bash
# Backend tests
cd backend
python -m pytest tests/

# Frontend type check
cd frontend
npx tsc --noEmit

# E2E tests
python -m pytest tests/e2e/
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [API Reference](docs/api-reference.md) | Complete API documentation |
| [User Guide](docs/user-guide.md) | End-user documentation |
| [Developer Guide](docs/developer-guide.md) | Development setup |
| [Architecture](docs/architecture.md) | System architecture |
| [Deployment Guide](docs/deployment.md) | Production deployment |
| [Testing Guide](docs/testing-guide.md) | Testing procedures |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Commit Convention

```
feat: add new feature
fix: fix bug
docs: update documentation
style: formatting changes
refactor: code refactoring
test: add tests
chore: maintenance tasks
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://reactjs.org/) - UI library
- [Recharts](https://recharts.org/) - Charting library
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM
- [Docker](https://www.docker.com/) - Containerization

---

<div align="center">

**[⬆ Back to top](#-foliobrake)**

</div>
