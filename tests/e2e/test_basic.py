import requests

def test_health():
    r = requests.get("http://localhost:8000/api/health")
    assert r.status_code == 200

def test_frontend():
    r = requests.get("http://localhost:1420")
    assert r.status_code == 200
