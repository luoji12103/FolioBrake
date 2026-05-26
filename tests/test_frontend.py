import requests

def test_frontend_loads():
    r = requests.get("http://localhost:1420")
    assert r.status_code == 200
    assert "FolioBrake" in r.text or "html" in r.text.lower()

def test_api_proxy():
    r = requests.get("http://localhost:1420/api/health")
    assert r.status_code == 200
