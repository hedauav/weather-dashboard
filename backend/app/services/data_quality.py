import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta, timezone
from typing import List, Dict, Any, Tuple
from collections import Counter
from app.config import settings

class DataQualityService:
    @staticmethod
    def is_leap_year(year: int) -> bool:
        return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

    @classmethod
    def clean_and_impute(
        cls,
        raw_observations: List[Dict[str, Any]],
        start_date: str,
        end_date: str,
        region_id: str
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Processes observations according to PRD section 6:
        - Detect & deduplicate (retain canonical observation)
        - Generate full expected calendar
        - Flag missing dates
        - Mode-first with median fallback imputation (window [-5, +5] days of valid originals)
        - Safety Rule: Imputed values are preserved separately and flagged so they CANNOT establish confirmed heatwaves.
        - Calculate coverage and gap warnings
        """
        # Step 1: Deduplication
        seen_dates = set()
        duplicates_count = 0
        canonical_map = {}
        
        for obs in raw_observations:
            d = obs["date"]
            if d in seen_dates:
                duplicates_count += 1
                # If conflicting, keep non-null original
                existing = canonical_map[d]
                if existing.get("temperature_max_original") is None and obs.get("temperature_max_original") is not None:
                    canonical_map[d] = obs
            else:
                seen_dates.add(d)
                canonical_map[d] = obs

        # Step 2: Generate complete calendar
        dt_start = datetime.strptime(start_date, "%Y-%m-%d").date()
        dt_end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        total_days = (dt_end - dt_start).days + 1
        expected_calendar = [dt_start + timedelta(days=i) for i in range(total_days)]
        
        indexed_records = []
        for d in expected_calendar:
            d_str = d.strftime("%Y-%m-%d")
            if d_str in canonical_map:
                obs = canonical_map[d_str]
                orig_val = obs.get("temperature_max_original")
                # Flag suspicious physical outliers (e.g. > 65C or < -90C)
                is_suspicious = False
                if orig_val is not None:
                    if orig_val > 65.0 or orig_val < -90.0:
                        is_suspicious = True
                
                indexed_records.append({
                    "date": d,
                    "date_str": d_str,
                    "temperature_max_original": orig_val if not is_suspicious else None,
                    "is_missing_date": False,
                    "quality_flags": ["suspicious_temperature"] if is_suspicious else []
                })
            else:
                indexed_records.append({
                    "date": d,
                    "date_str": d_str,
                    "temperature_max_original": None,
                    "is_missing_date": True,
                    "quality_flags": ["missing_calendar_date"]
                })

        # Step 3: Mode-first with median fallback imputation
        # Neighbor window: [-5 days, +5 days] using valid original observations only
        final_records = []
        total_imputed = 0
        missing_dates_count = sum(1 for r in indexed_records if r["is_missing_date"])

        for i, rec in enumerate(indexed_records):
            orig = rec["temperature_max_original"]
            rec_date = rec["date"]
            date_str = rec["date_str"]
            
            imputed_val = None
            is_imputed = False
            imputation_method = None
            
            if orig is None:
                # Search window in [-5, +5]
                window_left = max(0, i - 5)
                window_right = min(len(indexed_records), i + 6)
                
                neighbor_vals = [
                    indexed_records[j]["temperature_max_original"]
                    for j in range(window_left, window_right)
                    if j != i and indexed_records[j]["temperature_max_original"] is not None
                ]
                
                if neighbor_vals:
                    # Round continuous floats to 1 decimal place to inspect mode
                    rounded_vals = [round(v, 1) for v in neighbor_vals]
                    counts = Counter(rounded_vals)
                    top_two = counts.most_common(2)
                    
                    if len(top_two) == 1 or (len(top_two) > 1 and top_two[0][1] > top_two[1][1]):
                        # Unique mode exists
                        imputed_val = float(top_two[0][0])
                        imputation_method = "mode"
                    else:
                        # Fallback to median
                        imputed_val = float(np.median(neighbor_vals))
                        imputation_method = "median_fallback"
                    
                    is_imputed = True
                    total_imputed += 1

            final_records.append({
                "region_id": region_id,
                "date": date_str,
                "dataset": settings.DATASET_NAME,
                "source": "Open-Meteo ERA5",
                "temperature_max_original": orig,
                "temperature_max_imputed": imputed_val,
                "is_imputed": is_imputed,
                "imputation_method": imputation_method,
                "quality_flags": rec["quality_flags"],
                "is_missing_date": rec["is_missing_date"],
                "fetched_at": datetime.now(timezone.utc).isoformat()
            })

        # Step 4: Quality & Coverage Summary
        valid_original_count = sum(1 for r in final_records if r["temperature_max_original"] is not None)
        overall_coverage = (valid_original_count / total_days * 100.0) if total_days > 0 else 0.0

        # Gap detection
        long_gap_warnings = []
        consecutive_missing = 0
        max_missing_streak = 0
        gap_start = None

        for r in final_records:
            if r["temperature_max_original"] is None:
                if consecutive_missing == 0:
                    gap_start = r["date"]
                consecutive_missing += 1
            else:
                if consecutive_missing >= 5:
                    long_gap_warnings.append(f"Extended gap of {consecutive_missing} days starting on {gap_start}")
                max_missing_streak = max(max_missing_streak, consecutive_missing)
                consecutive_missing = 0

        if consecutive_missing >= 5:
            long_gap_warnings.append(f"Extended gap of {consecutive_missing} days starting on {gap_start}")
            max_missing_streak = max(max_missing_streak, consecutive_missing)

        quality_summary = {
            "total_expected_days": total_days,
            "total_valid_original_days": valid_original_count,
            "total_imputed_days": total_imputed,
            "total_missing_dates": missing_dates_count,
            "overall_coverage_pct": round(overall_coverage, 2),
            "long_gap_warnings": long_gap_warnings,
            "critical_event_gap_warnings": [
                f"Missing streak of {max_missing_streak} days detected; unconfirmed potential heat events may have been broken."
            ] if max_missing_streak >= 3 else [],
            "imputation_policy": settings.IMPUTATION_POLICY_VERSION,
            "duplicates_detected": duplicates_count
        }

        return final_records, quality_summary

    @classmethod
    def calculate_annual_coverage(cls, records: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
        """
        Computes coverage per calendar year:
        Coverage (%) = valid original daily observations / expected calendar days * 100
        Leap year expected = 366, normal = 365.
        Imputed values do not count towards coverage!
        """
        by_year: Dict[int, Dict[str, int]] = {}
        for r in records:
            yr = int(r["date"][:4])
            if yr not in by_year:
                by_year[yr] = {
                    "valid_original": 0,
                    "imputed": 0,
                    "missing": 0,
                    "total_in_data": 0
                }
            if r.get("temperature_max_original") is not None:
                by_year[yr]["valid_original"] += 1
            elif r.get("is_imputed"):
                by_year[yr]["imputed"] += 1
            else:
                by_year[yr]["missing"] += 1
            by_year[yr]["total_in_data"] += 1

        annual_stats = {}
        for yr, counts in sorted(by_year.items()):
            expected = 366 if cls.is_leap_year(yr) else 365
            valid_orig = counts["valid_original"]
            cov_pct = (valid_orig / expected) * 100.0
            is_eligible = cov_pct >= settings.COVERAGE_THRESHOLD_PERCENT
            
            exclusion_reason = None
            if not is_eligible:
                exclusion_reason = f"Coverage {cov_pct:.1f}% is below required {settings.COVERAGE_THRESHOLD_PERCENT}%"

            annual_stats[yr] = {
                "year": yr,
                "expected_days": expected,
                "valid_original_days": valid_orig,
                "imputed_days": counts["imputed"],
                "missing_days": expected - valid_orig,
                "data_coverage_pct": round(cov_pct, 2),
                "is_eligible_for_trend": is_eligible,
                "exclusion_reason": exclusion_reason
            }

        return annual_stats
