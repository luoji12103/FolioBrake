import requests

def test_api_proxy():
    r = requests.get("http://localhost:1420/api/health")
    assert r.status_code == 200
