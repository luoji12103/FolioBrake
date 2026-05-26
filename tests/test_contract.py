import requests

BASE_URL = "http://localhost:8000/api"

def test_health_contract():
    r = requests.get(f"{BASE_URL}/health")
    data = r.json()
    assert "status" in data
    assert "version" in data

def test_instruments_contract():
    r = requests.get(f"{BASE_URL}/data/instruments")
    data = r.json()
    assert isinstance(data, dict)
    assert "items" in data or isinstance(data, list)
