from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "Climate Hazard Trend Analyzer"
    API_V1_PREFIX: str = "/api/v1"
    
    # Dataset and baseline rules
    DATASET_NAME: str = "ERA5"
    BASELINE_START_YEAR: int = 1991
    BASELINE_END_YEAR: int = 2020
    DEFAULT_ANALYSIS_START_YEAR: int = 1990
    DEFAULT_ANALYSIS_END_YEAR: int = 2020
    THRESHOLD_PERCENTILE: float = 95.0
    MIN_CONSECUTIVE_DAYS: int = 3
    COVERAGE_THRESHOLD_PERCENT: float = 95.0
    
    # Imputation and Algorithm versioning
    IMPUTATION_POLICY_VERSION: str = "mode-first-median-fallback-v1"
    ALGORITHM_VERSION: str = "heatwave-linear-regression-v1"
    CACHE_TTL_SECONDS: int = 86400 * 7  # 7 days
    
    # Rate Limiting
    RATE_LIMIT_ANALYSIS: str = "30/minute"
    RATE_LIMIT_DEFAULT: str = "60/minute"
    
    # MongoDB Config
    MONGODB_URI: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "climate_analyzer_db"
    
    # Open-Meteo Config
    OPEN_METEO_ARCHIVE_URL: str = "https://archive-api.open-meteo.com/v1/archive"
    
    # CORS
    ALLOWED_ORIGINS: str = "*"


settings = Settings()
