import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_end_to_end_analysis_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "region_type": "city",
            "name": "Delhi",
            "start_date": "1990-01-01",
            "end_date": "2020-12-31",
            "hazard_type": "heatwave"
        }
        res = await ac.post("/api/v1/analysis", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "analysis_id" in data
        assert "temperature_threshold_celsius" in data
        assert data["temperature_threshold_celsius"] > 0
        assert len(data["annual_metrics"]) > 0
        assert "trend_metrics" in data
        assert "quality_summary" in data

        # Test cached retrieval
        anl_id = data["analysis_id"]
        res_cached = await ac.get(f"/api/v1/analysis/{anl_id}")
        assert res_cached.status_code == 200
