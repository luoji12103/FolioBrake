# Developer Guide

## Tech Stack
- **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.x, PostgreSQL 16, Redis 7
- **Frontend**: React 18, TypeScript, Vite, Recharts
- **Infrastructure**: Docker Compose, Prometheus, Celery

## Project Structure
```
backend/
  app/
    api/          # API endpoints
    core/         # Core utilities
    db/           # Database models
    services/     # Business logic
    analysis/     # Data analysis
    ml/           # Machine learning
frontend/
  src/
    components/   # React components
    pages/        # Page components
    hooks/        # Custom hooks
    api/          # API client
    utils/        # Utilities
```

## Development Workflow
1. Create feature branch
2. Implement changes
3. Run tests
4. Submit PR
