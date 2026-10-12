from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app

client = TestClient(app)

def test_health_check_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["dataset"] == "ERA5"
    assert "algorithm_version" in data

def test_get_preset_regions():
    response = client.get("/api/v1/regions/presets")
    assert response.status_code == 200
    data = response.json()
    assert "cities" in data
    assert "states" in data
    assert any(c["id"] == "delhi" for c in data["cities"])

def test_resolve_region_validation_error():
    # Missing required details
    response = client.post("/api/v1/regions/resolve", json={
        "region_type": "custom_bbox"
    })
    assert response.status_code == 422 or response.status_code == 400

def test_resolve_city_preset():
    response = client.post("/api/v1/regions/resolve", json={
        "region_type": "city",
        "name": "Delhi"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["region_type"] == "city"
    assert "Delhi" in data["name"]
    assert "grid-point" in data["sampling_method"]
