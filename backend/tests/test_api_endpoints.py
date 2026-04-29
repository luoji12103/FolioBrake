"""Smoke tests for all API endpoints. Run with: pytest backend/tests/test_api_endpoints.py -v

Tests marked with 'db' require a running PostgreSQL instance.
Set DATABASE_URL env var or run on the server where the stack is running.
"""

import os
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

requires_db = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not set — requires running PostgreSQL",
)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@requires_db
def test_instruments():
    response = client.get("/api/data/instruments")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@requires_db
def test_bars():
    response = client.get("/api/data/bars/510050?start_date=20250101&end_date=20251030")
    assert response.status_code in (200, 404)


@requires_db
def test_features_definitions():
    response = client.get("/api/features/definitions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 17


@requires_db
def test_risk_state():
    response = client.get("/api/risk/state")
    assert response.status_code == 200
    assert "state" in response.json()


@requires_db
def test_risk_overlay():
    response = client.get("/api/risk/overlay")
    assert response.status_code == 200
    assert "decision" in response.json()


@requires_db
def test_strategy_signals():
    response = client.get("/api/strategy/signals")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@requires_db
def test_strategy_portfolio():
    response = client.get("/api/strategy/portfolio")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@requires_db
def test_paper_pnl():
    response = client.get("/api/paper/pnl/1")
    assert response.status_code in (200, 404)


@requires_db
def test_backtest_results():
    response = client.get("/api/backtest/results/1")
    assert response.status_code in (200, 404)


# Unit tests (no DB required)

def test_constraint_concentration():
    from app.strategy.constraints import apply_concentration_limit
    portfolio = [
        {"instrument_id": 1, "target_weight": 0.50},
        {"instrument_id": 2, "target_weight": 0.30},
        {"instrument_id": 3, "target_weight": 0.20},
    ]
    result = apply_concentration_limit(portfolio, max_weight=0.30)
    # Total weight should stay ~1.0
    total = sum(p["target_weight"] for p in result)
    assert 0.99 <= total <= 1.01
    # The originally overweight position should be reduced
    assert result[0]["target_weight"] < 0.50


def test_constraint_turnover():
    from app.strategy.constraints import apply_turnover_limit
    portfolio = [
        {"instrument_id": 1, "target_weight": 0.80},
        {"instrument_id": 2, "target_weight": 0.20},
    ]
    prev = {1: 0.20, 2: 0.80}  # 60% turnover each way = 120% total / 2 = 60% half-turnover
    result = apply_turnover_limit(portfolio, prev, max_turnover=0.30)
    total_move = sum(abs(p["target_weight"] - prev.get(p["instrument_id"], 0)) for p in result)
    # Half-turnover should not exceed max_turnover
    assert total_move / 2 <= 0.30 + 0.01  # small float tolerance


def test_constraint_min_positions():
    from app.strategy.constraints import apply_min_positions
    portfolio = [{"instrument_id": i, "target_weight": 0.005} for i in range(5)]
    result = apply_min_positions(portfolio, min_count=3)
    non_zero = [p for p in result if p["target_weight"] >= 0.01]
    assert len(non_zero) >= 3


def test_backtest_metrics():
    from app.backtest.metrics import compute_sharpe, compute_max_drawdown, compute_cagr
    equity = [100.0 + i * 0.1 for i in range(100)]
    returns = [0.001] * 99
    assert compute_sharpe(returns) > 0
    assert compute_max_drawdown(equity) <= 0
    assert compute_cagr(equity, 99) > 0
