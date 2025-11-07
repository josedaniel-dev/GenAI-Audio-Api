import pytest
from fastapi.testclient import TestClient
from fastapi_server import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()

def test_cache_summary_endpoint():
    response = client.get("/cache/summary")
    assert response.status_code == 200
    assert "total_stems" in response.json()
