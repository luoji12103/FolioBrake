import requests

def test_api_health():
    r = requests.get("http://localhost:8000/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_frontend_loads():
    r = requests.get("http://localhost:1420")
    assert r.status_code == 200
