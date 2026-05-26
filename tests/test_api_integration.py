import requests
import pytest

BASE_URL = "http://localhost:8000/api"

def test_health():
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_instruments():
    r = requests.get(f"{BASE_URL}/data/instruments")
    assert r.status_code == 200

def test_signals():
    r = requests.get(f"{BASE_URL}/strategy/signals")
    assert r.status_code == 200

def test_risk_state():
    r = requests.get(f"{BASE_URL}/risk/state")
    assert r.status_code == 200

def test_paper_portfolios():
    r = requests.get(f"{BASE_URL}/paper/portfolios")
    assert r.status_code == 200

def test_analysis():
    r = requests.get(f"{BASE_URL}/analysis/drawdown/510050")
    assert r.status_code == 200
