import requests
import time

def test_api_response_time():
    start = time.time()
    r = requests.get("http://localhost:8000/api/health")
    elapsed = time.time() - start
    assert r.status_code == 200
    assert elapsed < 1.0  # Should respond within 1 second

def test_instruments_response_time():
    start = time.time()
    r = requests.get("http://localhost:8000/api/data/instruments")
    elapsed = time.time() - start
    assert r.status_code == 200
    assert elapsed < 2.0  # Should respond within 2 seconds
