import hashlib
import json
import logging
from datetime import datetime, date
from typing import Dict, Any, List
from app.config import settings
from app.schemas import (
    AnalysisRequest,
    AnalysisResponse,
    ResolvedRegion,
    AnnualMetric,
    HeatwaveEvent,
    TrendMetrics,
    QualitySummary
)
from app.database import db_manager
from app.services.weather_service import WeatherService
from app.services.data_quality import DataQualityService
from app.services.hazard_detector import HazardDetector
from app.services.trend_analyzer import TrendAnalyzer

logger = logging.getLogger(__name__)

class AnalysisService:
    @staticmethod
    def generate_cache_key(
        region_id: str,
        start_date: str,
        end_date: str,
        hazard_type: str
    ) -> str:
        """
        PRD 9.3: Cache key includes all settings affecting results:
        region, date range, dataset, baseline, algorithm version, imputation policy.
        """
        raw = f"{region_id}|{start_date}|{end_date}|{hazard_type}|{settings.DATASET_NAME}|{settings.BASELINE_START_YEAR}-{settings.BASELINE_END_YEAR}|{settings.ALGORITHM_VERSION}|{settings.IMPUTATION_POLICY_VERSION}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @classmethod
    async def perform_analysis(cls, req: AnalysisRequest) -> AnalysisResponse:
        # 1. Resolve region
        resolved_dict = WeatherService.resolve_region(
            region_type=req.region_type,
            name=req.name,
            latitude=req.latitude,
            longitude=req.longitude,
            bounding_box=req.bounding_box
        )
        region = ResolvedRegion(**resolved_dict)
        await db_manager.save_region(resolved_dict)

        start_str = req.start_date.strftime("%Y-%m-%d")
        end_str = req.end_date.strftime("%Y-%m-%d")
        cache_key = cls.generate_cache_key(region.region_id, start_str, end_str, req.hazard_type)

        # 2. Check cached analysis
        cached_doc = await db_manager.get_cached_analysis(cache_key)
        if cached_doc:
            logger.info(f"Analysis Cache HIT for key: {cache_key}")
            cached_doc["is_cached"] = True
            return AnalysisResponse(**cached_doc)

        logger.info(f"Analysis Cache MISS for key: {cache_key}. Proceeding with computation.")

        # 3. Baseline Data Fetch & Threshold
        # Baseline is 1991-01-01 to 2020-12-31
        baseline_start_str = f"{settings.BASELINE_START_YEAR}-01-01"
        baseline_end_str = f"{settings.BASELINE_END_YEAR}-12-31"

        # Check weather records in DB for baseline
        baseline_records = await db_manager.get_weather_records(
            region_id=region.region_id,
            dataset=settings.DATASET_NAME,
            start_date=baseline_start_str,
            end_date=baseline_end_str
        )

        if not baseline_records:
            # Ingest baseline from Open-Meteo
            raw_baseline = await WeatherService.fetch_open_meteo_era5(
                latitude=region.latitude,
                longitude=region.longitude,
                start_date=baseline_start_str,
                end_date=baseline_end_str
            )
            clean_baseline, _ = DataQualityService.clean_and_impute(
                raw_baseline,
                baseline_start_str,
                baseline_end_str,
                region.region_id
            )
            await db_manager.save_weather_records(clean_baseline)
            baseline_records = clean_baseline

        threshold_t95 = HazardDetector.calculate_baseline_threshold(
            baseline_records=baseline_records,
            percentile=settings.THRESHOLD_PERCENTILE
        )

        # 4. Analysis Period Data Fetch
        # Check if requested period is completely covered inside baseline
        analysis_records = []
        if req.start_date.year >= settings.BASELINE_START_YEAR and req.end_date.year <= settings.BASELINE_END_YEAR:
            # Slice from already cleaned baseline
            analysis_records = [
                r for r in baseline_records
                if start_str <= r["date"] <= end_str
            ]
        else:
            # Check DB or fetch from Open-Meteo
            existing_recs = await db_manager.get_weather_records(
                region.region_id, settings.DATASET_NAME, start_str, end_str
            )
            if existing_recs and len(existing_recs) >= (req.end_date - req.start_date).days + 1:
                analysis_records = existing_recs
            else:
                raw_analysis = await WeatherService.fetch_open_meteo_era5(
                    latitude=region.latitude,
                    longitude=region.longitude,
                    start_date=start_str,
                    end_date=end_str
                )
                clean_analysis, _ = DataQualityService.clean_and_impute(
                    raw_analysis,
                    start_str,
                    end_str,
                    region.region_id
                )
                await db_manager.save_weather_records(clean_analysis)
                analysis_records = clean_analysis

        # 5. Data Quality, Missing-Values and Annual Coverage
        # Run clean_and_impute to ensure complete calendar & gap markers
        final_records, quality_summary_dict = DataQualityService.clean_and_impute(
            analysis_records, start_str, end_str, region.region_id
        )
        annual_cov_map = DataQualityService.calculate_annual_coverage(final_records)

        # 6. Heatwave Event Detection
        events_raw, annual_hazard_map = HazardDetector.detect_heatwaves(
            records=final_records,
            threshold=threshold_t95,
            min_consecutive_days=settings.MIN_CONSECUTIVE_DAYS
        )

        events: List[HeatwaveEvent] = [HeatwaveEvent(**e) for e in events_raw]

        # 7. Merge annual coverage and hazard metrics
        annual_metrics: List[AnnualMetric] = []
        all_years = sorted(list(set(list(annual_cov_map.keys()) + list(annual_hazard_map.keys()))))

        for yr in all_years:
            cov = annual_cov_map.get(yr, {})
            haz = annual_hazard_map.get(yr, {})

            expected_days = cov.get("expected_days", 366 if DataQualityService.is_leap_year(yr) else 365)
            valid_days = cov.get("valid_original_days", 0)
            cov_pct = cov.get("data_coverage_pct", 0.0)
            is_eligible = cov.get("is_eligible_for_trend", False)

            annual_metrics.append(AnnualMetric(
                year=yr,
                event_count=haz.get("event_count", 0),
                heatwave_days=haz.get("heatwave_days", 0),
                mean_duration=haz.get("mean_duration", 0.0),
                max_duration=haz.get("max_duration", 0),
                data_coverage_pct=cov_pct,
                expected_days=expected_days,
                valid_original_days=valid_days,
                imputed_days=cov.get("imputed_days", 0),
                missing_days=expected_days - valid_days,
                is_eligible_for_trend=is_eligible,
                exclusion_reason=cov.get("exclusion_reason")
            ))

        # 8. Trend Analysis and dynamic insights
        trend_metrics = TrendAnalyzer.calculate_trend_and_rolling(annual_metrics)
        insights = TrendAnalyzer.generate_summary_insights(
            trend_metrics=trend_metrics,
            annual_metrics=annual_metrics,
            threshold=threshold_t95,
            total_events=len(events)
        )

        analysis_id = f"anl_{cache_key[:12]}"
        created_at_str = datetime.utcnow().isoformat()

        response_obj = AnalysisResponse(
            analysis_id=analysis_id,
            cache_key=cache_key,
            is_cached=False,
            region=region,
            requested_period={"start_date": start_str, "end_date": end_str},
            dataset_metadata={
                "dataset_name": settings.DATASET_NAME,
                "source": "Open-Meteo Historical Weather Archive",
                "variable": "temperature_2m_max",
                "spatial_resolution": "0.25° grid (~31km)"
            },
            baseline_metadata={
                "baseline_period": f"{settings.BASELINE_START_YEAR}–{settings.BASELINE_END_YEAR}",
                "threshold_rule": f"Fixed pooled {settings.THRESHOLD_PERCENTILE}th percentile of baseline daily Tmax",
                "disclaimer": "Historical trends are relative to the 1991–2020 baseline and do not establish direct climate change attribution."
            },
            temperature_threshold_celsius=threshold_t95,
            annual_metrics=annual_metrics,
            events=events,
            trend_metrics=trend_metrics,
            quality_summary=QualitySummary(**quality_summary_dict),
            summary_insights=insights,
            created_at=created_at_str
        )

        # 9. Save to Analysis Cache (TTL 7 days)
        cache_doc = response_obj.model_dump(mode="json")
        cache_doc["expires_at"] = datetime.utcnow().timestamp() + settings.CACHE_TTL_SECONDS
        await db_manager.save_cached_analysis(cache_doc)

        return response_obj
