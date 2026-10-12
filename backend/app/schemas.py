from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional, Dict, Any, Literal
from datetime import date


class BoundingBox(BaseModel):
    min_lat: float = Field(..., description="Minimum latitude (-90 to 90)")
    max_lat: float = Field(..., description="Maximum latitude (-90 to 90)")
    min_lon: float = Field(..., description="Minimum longitude (-180 to 180)")
    max_lon: float = Field(..., description="Maximum longitude (-180 to 180)")

    @model_validator(mode="after")
    def validate_bounds(self):
        if not (-90.0 <= self.min_lat <= 90.0 and -90.0 <= self.max_lat <= 90.0):
            raise ValueError("Latitudes must be between -90 and 90 degrees.")
        if not (-180.0 <= self.min_lon <= 180.0 and -180.0 <= self.max_lon <= 180.0):
            raise ValueError("Longitudes must be between -180 and 180 degrees.")
        if self.min_lat > self.max_lat:
            raise ValueError("min_lat cannot be greater than max_lat.")
        if self.min_lon > self.max_lon:
            raise ValueError("min_lon cannot be greater than max_lon.")
        if (self.max_lat - self.min_lat) > 10.0 or (self.max_lon - self.min_lon) > 10.0:
            raise ValueError("Bounding box span too large (max allowed span 10x10 degrees for API safety).")
        return self


class RegionResolveRequest(BaseModel):
    region_type: Literal["city", "state", "custom_bbox"]
    name: Optional[str] = Field(None, description="City or State name")
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    bounding_box: Optional[BoundingBox] = None

    @model_validator(mode="after")
    def validate_region(self):
        if self.region_type in ("city", "state"):
            if not self.name and (self.latitude is None or self.longitude is None):
                raise ValueError("Must provide either a name or (latitude, longitude) for city/state.")
        elif self.region_type == "custom_bbox":
            if not self.bounding_box:
                raise ValueError("bounding_box is required when region_type is 'custom_bbox'.")
        return self


class ResolvedRegion(BaseModel):
    region_id: str
    name: str
    region_type: Literal["city", "state", "custom_bbox"]
    latitude: float
    longitude: float
    bounding_box: Optional[BoundingBox] = None
    sampling_method: str = "grid-point approximation"
    spatial_disclosure: str


class AnalysisRequest(BaseModel):
    region_type: Literal["city", "state", "custom_bbox"]
    name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    bounding_box: Optional[BoundingBox] = None
    start_date: date = Field(default=date(1990, 1, 1))
    end_date: date = Field(default=date(2020, 12, 31))
    hazard_type: Literal["heatwave"] = "heatwave"

    @model_validator(mode="after")
    def validate_dates_and_region(self):
        if self.start_date > self.end_date:
            raise ValueError("start_date cannot be after end_date.")
        if self.start_date.year < 1950:
            raise ValueError("Analysis before 1950 is not supported in this ERA5 archive view.")
        if self.end_date > date.today():
            raise ValueError("end_date cannot be in the future.")
        if self.region_type in ("city", "state"):
            if not self.name and (self.latitude is None or self.longitude is None):
                raise ValueError("Must provide name or coordinates for city/state.")
        elif self.region_type == "custom_bbox" and not self.bounding_box:
            raise ValueError("bounding_box is required for custom_bbox.")
        return self


class HeatwaveEvent(BaseModel):
    event_id: str
    start_date: date
    end_date: date
    duration_days: int
    max_temperature: float
    threshold: float
    excess_temperature: float
    crossing_years: List[int]
    status: Literal["confirmed", "uncertain"] = "confirmed"


class AnnualMetric(BaseModel):
    year: int
    event_count: int
    heatwave_days: int
    mean_duration: float
    max_duration: int
    data_coverage_pct: float
    expected_days: int
    valid_original_days: int
    imputed_days: int
    missing_days: int
    is_eligible_for_trend: bool
    exclusion_reason: Optional[str] = None


class TrendMetrics(BaseModel):
    slope: float  # events per year
    rolling_average_5yr: Dict[int, Optional[float]]
    total_years: int
    eligible_years: int
    excluded_years: List[int]
    trend_description: str
    percentage_change: Optional[float] = None
    percentage_change_note: Optional[str] = None


class QualitySummary(BaseModel):
    total_expected_days: int
    total_valid_original_days: int
    total_imputed_days: int
    total_missing_dates: int
    overall_coverage_pct: float
    long_gap_warnings: List[str]
    critical_event_gap_warnings: List[str]
    imputation_policy: str
    duplicates_detected: int


class AnalysisResponse(BaseModel):
    analysis_id: str
    cache_key: str
    is_cached: bool
    region: ResolvedRegion
    requested_period: Dict[str, str]
    dataset_metadata: Dict[str, Any]
    baseline_metadata: Dict[str, Any]
    temperature_threshold_celsius: float
    annual_metrics: List[AnnualMetric]
    events: List[HeatwaveEvent]
    trend_metrics: TrendMetrics
    quality_summary: QualitySummary
    summary_insights: List[str]
    created_at: str


class CoverageResponse(BaseModel):
    region_id: str
    start_date: date
    end_date: date
    annual_coverage: List[Dict[str, Any]]
    quality_summary: QualitySummary
