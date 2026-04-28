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
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@requires_db
def test_instruments():
    response = client.get("/data/instruments")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@requires_db
def test_bars():
    response = client.get("/data/bars/510050?start_date=20250101&end_date=20251030")
    assert response.status_code in (200, 404)


@requires_db
def test_features_definitions():
    response = client.get("/features/definitions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@requires_db
def test_risk_state():
    response = client.get("/risk/state")
    assert response.status_code == 200
    assert "state" in response.json()


@requires_db
def test_risk_overlay():
    response = client.get("/risk/overlay")
    assert response.status_code == 200
    assert "decision" in response.json()


@requires_db
def test_strategy_signals():
    response = client.get("/strategy/signals")
    assert response.status_code == 200


@requires_db
def test_strategy_portfolio():
    response = client.get("/strategy/portfolio")
    assert response.status_code == 200


@requires_db
def test_paper_pnl():
    response = client.get("/paper/pnl/1")
    assert response.status_code == 200
    assert "pnl" in response.json()


@requires_db
def test_backtest_results():
    response = client.get("/backtest/results/1")
    assert response.status_code in (200, 404)
