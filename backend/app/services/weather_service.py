import httpx
import logging
import asyncio
from datetime import date
from typing import List, Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)

# Predefined coordinates for common world and Indian cities / states for instant lookup
PRESET_CITIES = {
    "delhi": {"lat": 28.6139, "lon": 77.2090, "name": "Delhi, India"},
    "mumbai": {"lat": 19.0760, "lon": 72.8777, "name": "Mumbai, India"},
    "london": {"lat": 51.5074, "lon": -0.1278, "name": "London, UK"},
    "new york": {"lat": 40.7128, "lon": -74.0060, "name": "New York, USA"},
    "paris": {"lat": 48.8566, "lon": 2.3522, "name": "Paris, France"},
    "tokyo": {"lat": 35.6762, "lon": 139.6503, "name": "Tokyo, Japan"},
    "sydney": {"lat": -33.8688, "lon": 151.2093, "name": "Sydney, Australia"},
    "cairo": {"lat": 30.0444, "lon": 31.2357, "name": "Cairo, Egypt"},
    "bangalore": {"lat": 12.9716, "lon": 77.5946, "name": "Bengaluru, India"},
    "ahmedabad": {"lat": 23.0225, "lon": 72.5714, "name": "Ahmedabad, India"},
    "kolkata": {"lat": 22.5726, "lon": 88.3639, "name": "Kolkata, India"},
    "phoenix": {"lat": 33.4484, "lon": -112.0740, "name": "Phoenix, USA"},
    "madrid": {"lat": 40.4168, "lon": -3.7038, "name": "Madrid, Spain"},
    "nagpur": {"lat": 21.1458, "lon": 79.0882, "name": "Nagpur, India"},
}

PRESET_STATES = {
    "california": {"lat": 36.7783, "lon": -119.4179, "name": "California (Centroid), USA"},
    "texas": {"lat": 31.9686, "lon": -99.9018, "name": "Texas (Centroid), USA"},
    "rajasthan": {"lat": 27.0238, "lon": 74.2179, "name": "Rajasthan (Centroid), India"},
    "maharashtra": {"lat": 19.7515, "lon": 75.7139, "name": "Maharashtra (Centroid), India"},
    "florida": {"lat": 27.6648, "lon": -81.5158, "name": "Florida (Centroid), USA"},
    "andalusia": {"lat": 37.5443, "lon": -4.7278, "name": "Andalusia (Centroid), Spain"},
}


class WeatherService:
    @staticmethod
    def resolve_region(
        region_type: str,
        name: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        bounding_box: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Resolves region to canonical coordinates and deterministic ID."""
        cleaned_name = name.strip() if name else ""
        lower_name = cleaned_name.lower()
        
        if region_type == "city":
            if lower_name in PRESET_CITIES:
                resolved_lat = PRESET_CITIES[lower_name]["lat"]
                resolved_lon = PRESET_CITIES[lower_name]["lon"]
                display_name = PRESET_CITIES[lower_name]["name"]
            elif latitude is not None and longitude is not None:
                resolved_lat = round(latitude, 4)
                resolved_lon = round(longitude, 4)
                display_name = cleaned_name or f"City ({resolved_lat}, {resolved_lon})"
            else:
                raise ValueError(f"Unknown city '{name}'. Please provide coordinates.")
            
            region_id = f"city_{resolved_lat:.4f}_{resolved_lon:.4f}"
            return {
                "region_id": region_id,
                "name": display_name,
                "region_type": "city",
                "latitude": resolved_lat,
                "longitude": resolved_lon,
                "bounding_box": None,
                "sampling_method": "grid-point approximation",
                "spatial_disclosure": "Observations represent a single ERA5 reanalysis grid point nearest to city coordinates."
            }

        elif region_type == "state":
            if lower_name in PRESET_STATES:
                resolved_lat = PRESET_STATES[lower_name]["lat"]
                resolved_lon = PRESET_STATES[lower_name]["lon"]
                display_name = PRESET_STATES[lower_name]["name"]
            elif latitude is not None and longitude is not None:
                resolved_lat = round(latitude, 4)
                resolved_lon = round(longitude, 4)
                display_name = cleaned_name or f"State Centroid ({resolved_lat}, {resolved_lon})"
            else:
                raise ValueError(f"Unknown state '{name}'. Please provide coordinates.")
            
            region_id = f"state_{resolved_lat:.4f}_{resolved_lon:.4f}"
            return {
                "region_id": region_id,
                "name": display_name,
                "region_type": "state",
                "latitude": resolved_lat,
                "longitude": resolved_lon,
                "bounding_box": None,
                "sampling_method": "representative state centroid grid point",
                "spatial_disclosure": "Disclosed limitation: ERA5 data sampled at representative state centroid rather than whole-state spatial average."
            }

        elif region_type == "custom_bbox":
            if not bounding_box:
                raise ValueError("bounding_box is missing")
            # Sample midpoint or 4 corners grid average
            mid_lat = round((bounding_box.min_lat + bounding_box.max_lat) / 2.0, 4)
            mid_lon = round((bounding_box.min_lon + bounding_box.max_lon) / 2.0, 4)
            region_id = f"bbox_{bounding_box.min_lat:.2f}_{bounding_box.max_lat:.2f}_{bounding_box.min_lon:.2f}_{bounding_box.max_lon:.2f}"
            display_name = f"Bounding Box [{bounding_box.min_lat:.2f}, {bounding_box.min_lon:.2f} to {bounding_box.max_lat:.2f}, {bounding_box.max_lon:.2f}]"
            
            return {
                "region_id": region_id,
                "name": display_name,
                "region_type": "custom_bbox",
                "latitude": mid_lat,
                "longitude": mid_lon,
                "bounding_box": bounding_box.model_dump() if hasattr(bounding_box, "model_dump") else bounding_box,
                "sampling_method": "centroid grid point sampling of bounding box",
                "spatial_disclosure": "Grid-point sampled at bounding box center with bounds validated."
            }
        else:
            raise ValueError(f"Unsupported region type: {region_type}")

    @staticmethod
    async def fetch_open_meteo_era5(
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        retries: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Fetches historical daily maximum temperature (temperature_2m_max) from Open-Meteo ERA5 archive.
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "daily": "temperature_2m_max",
            "timezone": "UTC",
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            last_err = None
            for attempt in range(1, retries + 1):
                try:
                    logger.info(f"Fetching Open-Meteo ERA5 ({latitude}, {longitude}) from {start_date} to {end_date} (Attempt {attempt})")
                    resp = await client.get(settings.OPEN_METEO_ARCHIVE_URL, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        daily = data.get("daily", {})
                        dates = daily.get("time", [])
                        t_max = daily.get("temperature_2m_max", [])
                        
                        if not dates:
                            logger.warning("Open-Meteo returned empty daily time array.")
                            return []
                        
                        observations = []
                        for d_str, temp in zip(dates, t_max):
                            observations.append({
                                "date": d_str,
                                "temperature_max_original": float(temp) if temp is not None else None,
                                "dataset": settings.DATASET_NAME,
                                "source": "Open-Meteo ERA5"
                            })
                        return observations
                    elif resp.status_code in (429, 502, 503, 504):
                        await asyncio.sleep(attempt * 1.5)
                        last_err = f"Open-Meteo HTTP {resp.status_code}: {resp.text}"
                    else:
                        raise ValueError(f"Open-Meteo API returned {resp.status_code}: {resp.text}")
                except httpx.RequestError as exc:
                    last_err = str(exc)
                    await asyncio.sleep(attempt * 1.0)
            
            raise RuntimeError(f"Failed to fetch data from Open-Meteo after {retries} attempts. Cause: {last_err}")
