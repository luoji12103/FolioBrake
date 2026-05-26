# Testing Guide

## Running Tests
```bash
# Backend tests
python -m pytest tests/

# Frontend type check
cd frontend && npx tsc --noEmit

# E2E tests
python -m pytest tests/e2e/
```

## Test Types
- **Unit tests**: Test individual functions
- **Integration tests**: Test API endpoints
- **E2E tests**: Test full user flows
- **Performance tests**: Test response times
