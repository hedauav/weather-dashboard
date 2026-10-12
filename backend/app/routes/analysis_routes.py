from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, Any, List
from app.schemas import (
    RegionResolveRequest,
    ResolvedRegion,
    AnalysisRequest,
    AnalysisResponse,
    CoverageResponse
)
from app.services.weather_service import WeatherService, PRESET_CITIES, PRESET_STATES
from app.services.analysis_service import AnalysisService
from app.database import db_manager

router = APIRouter()

@router.get("/regions/presets", response_model=Dict[str, Any])
async def get_preset_regions():
    """Returns curated preset cities and states for one-click selection."""
    return {
        "cities": [
            {"id": k, "name": v["name"], "lat": v["lat"], "lon": v["lon"]}
            for k, v in PRESET_CITIES.items()
        ],
        "states": [
            {"id": k, "name": v["name"], "lat": v["lat"], "lon": v["lon"]}
            for k, v in PRESET_STATES.items()
        ]
    }

@router.post("/regions/resolve", response_model=ResolvedRegion)
async def resolve_region(req: RegionResolveRequest):
    """
    Validates and resolves region coordinates and returns a deterministic region ID.
    Discloses approximations and centroid sampling.
    """
    try:
        resolved = WeatherService.resolve_region(
            region_type=req.region_type,
            name=req.name,
            latitude=req.latitude,
            longitude=req.longitude,
            bounding_box=req.bounding_box
        )
        return ResolvedRegion(**resolved)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve region: {str(e)}")

@router.post("/analysis", response_model=AnalysisResponse)
async def trigger_analysis(req: AnalysisRequest):
    """
    Retrieves or calculates heatwave analysis against ERA5 baseline.
    Checks cache first, ingests data, validates quality, detects events,
    calculates trends and returns rich analytical output.
    """
    try:
        result = await AnalysisService.perform_analysis(req)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except RuntimeError as re:
        raise HTTPException(status_code=502, detail=str(re))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis pipeline error: {str(e)}")

@router.get("/analysis/{analysis_id}", response_model=AnalysisResponse)
async def get_cached_analysis_by_id(analysis_id: str):
    """Retrieves an existing cached analysis by its unique analysis ID."""
    # Find matching analysis in database cache
    if db_manager._in_memory_cache:
        for val in db_manager._in_memory_cache.values():
            if val.get("analysis_id") == analysis_id:
                return AnalysisResponse(**val)
    if db_manager.is_connected and db_manager.db is not None:
        doc = await db_manager.db.analysis_cache.find_one({"analysis_id": analysis_id})
        if doc:
            doc.pop("_id", None)
            return AnalysisResponse(**doc)
            
    raise HTTPException(status_code=404, detail=f"Analysis with ID {analysis_id} not found.")

@router.get("/regions/{region_id}/coverage")
async def get_region_coverage(region_id: str):
    """Returns coverage and quality info for a previously processed region."""
    records = await db_manager.get_weather_records(
        region_id=region_id,
        dataset="ERA5",
        start_date="1950-01-01",
        end_date="2030-12-31"
    )
    if not records:
        raise HTTPException(status_code=404, detail="No weather records stored for this region.")
    
    from app.services.data_quality import DataQualityService
    annual_cov = DataQualityService.calculate_annual_coverage(records)
    return {
        "region_id": region_id,
        "total_records": len(records),
        "annual_coverage": annual_cov
    }
