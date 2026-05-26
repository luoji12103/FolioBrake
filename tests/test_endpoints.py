import requests

BASE_URL = "http://localhost:8000/api"

def test_health_endpoint():
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200
    assert "status" in r.json()

def test_instruments_endpoint():
    r = requests.get(f"{BASE_URL}/data/instruments")
    assert r.status_code == 200
    assert isinstance(r.json(), dict)
