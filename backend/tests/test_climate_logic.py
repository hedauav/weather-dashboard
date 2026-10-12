import pytest
from datetime import date
from app.services.hazard_detector import HazardDetector
from app.services.data_quality import DataQualityService
from app.services.trend_analyzer import TrendAnalyzer
from app.schemas import AnnualMetric

# 1. Three consecutive qualifying days produce one event
def test_three_consecutive_qualifying_days_produce_one_event():
    threshold = 35.0
    records = [
        {"date": "2000-06-01", "temperature_max_original": 36.0},
        {"date": "2000-06-02", "temperature_max_original": 37.0},
        {"date": "2000-06-03", "temperature_max_original": 36.5},
        {"date": "2000-06-04", "temperature_max_original": 30.0},
    ]
    events, stats = HazardDetector.detect_heatwaves(records, threshold)
    assert len(events) == 1
    assert events[0]["duration_days"] == 3
    assert events[0]["max_temperature"] == 37.0
    assert stats[2000]["event_count"] == 1
    assert stats[2000]["heatwave_days"] == 3

# 2. Two qualifying days do NOT produce an event
def test_two_qualifying_days_do_not_produce_event():
    threshold = 35.0
    records = [
        {"date": "2000-06-01", "temperature_max_original": 36.0},
        {"date": "2000-06-02", "temperature_max_original": 37.0},
        {"date": "2000-06-03", "temperature_max_original": 34.0},
    ]
    events, stats = HazardDetector.detect_heatwaves(records, threshold)
    assert len(events) == 0
    assert stats[2000]["event_count"] == 0
    assert stats[2000]["heatwave_days"] == 0

# 3. Four or more qualifying days form one continuous event
def test_four_or_more_days_form_one_continuous_event():
    threshold = 35.0
    records = [
        {"date": "2000-06-01", "temperature_max_original": 36.0},
        {"date": "2000-06-02", "temperature_max_original": 37.0},
        {"date": "2000-06-03", "temperature_max_original": 38.0},
        {"date": "2000-06-04", "temperature_max_original": 39.0},
        {"date": "2000-06-05", "temperature_max_original": 32.0},
    ]
    events, stats = HazardDetector.detect_heatwaves(records, threshold)
    assert len(events) == 1
    assert events[0]["duration_days"] == 4
    assert events[0]["max_temperature"] == 39.0

# 4. A missing day breaks a confirmed sequence
def test_missing_day_breaks_confirmed_sequence():
    threshold = 35.0
    # Day 2 is missing
    records = [
        {"date": "2000-06-01", "temperature_max_original": 36.0},
        {"date": "2000-06-02", "temperature_max_original": None},
        {"date": "2000-06-03", "temperature_max_original": 36.5},
        {"date": "2000-06-04", "temperature_max_original": 37.0},
    ]
    events, stats = HazardDetector.detect_heatwaves(records, threshold)
    # The first streak has 1 day (broken). The second has 2 days (broken). Neither reaches 3.
    assert len(events) == 0

# 5. An imputed temperature CANNOT establish an event
def test_imputed_temperature_cannot_establish_event():
    threshold = 35.0
    # Day 2 has an imputed temp of 38.0, but original is None
    records = [
        {"date": "2000-06-01", "temperature_max_original": 36.0, "is_imputed": False},
        {"date": "2000-06-02", "temperature_max_original": None, "temperature_max_imputed": 38.0, "is_imputed": True},
        {"date": "2000-06-03", "temperature_max_original": 37.0, "is_imputed": False},
    ]
    events, stats = HazardDetector.detect_heatwaves(records, threshold)
    assert len(events) == 0

# 6. Event crossing year boundary
def test_event_crossing_year_boundary():
    threshold = 30.0
    records = [
        {"date": "2000-12-30", "temperature_max_original": 32.0},
        {"date": "2000-12-31", "temperature_max_original": 33.0},
        {"date": "2001-01-01", "temperature_max_original": 34.0},
        {"date": "2001-01-02", "temperature_max_original": 32.0},
        {"date": "2001-01-03", "temperature_max_original": 25.0},
    ]
    events, stats = HazardDetector.detect_heatwaves(records, threshold)
    # Single continuous event
    assert len(events) == 1
    assert events[0]["duration_days"] == 4
    # Event count attributed to start year (2000)
    assert stats[2000]["event_count"] == 1
    assert stats[2001]["event_count"] == 0
    # Days allocated to respective years (2 in 2000, 2 in 2001)
    assert stats[2000]["heatwave_days"] == 2
    assert stats[2001]["heatwave_days"] == 2

# 7. Deduplication does not inflate event counts
def test_deduplication():
    raw = [
        {"date": "2000-06-01", "temperature_max_original": 36.0},
        {"date": "2000-06-01", "temperature_max_original": 36.0}, # duplicate
        {"date": "2000-06-02", "temperature_max_original": 37.0},
        {"date": "2000-06-03", "temperature_max_original": 38.0},
    ]
    cleaned, summary = DataQualityService.clean_and_impute(raw, "2000-06-01", "2000-06-03", "test_reg")
    assert summary["duplicates_detected"] == 1
    assert len(cleaned) == 3

# 8. Leap years use 366 expected calendar days
def test_leap_year_expected_days():
    assert DataQualityService.is_leap_year(2000) is True
    assert DataQualityService.is_leap_year(2004) is True
    assert DataQualityService.is_leap_year(1900) is False
    assert DataQualityService.is_leap_year(2001) is False

# 9. Coverage at exactly 95% is eligible
def test_coverage_at_95_percent_is_eligible():
    records = []
    # 365 days in 2001. 95% is 346.75 -> 347 days needed
    for i in range(1, 366):
        d_str = f"2001-01-01" # dummy date pattern
        is_valid = i <= 347
        records.append({
            "date": f"2001-{(i%12)+1:02d}-{(i%28)+1:02d}",
            "temperature_max_original": 25.0 if is_valid else None
        })
    cov = DataQualityService.calculate_annual_coverage(records)
    assert cov[2001]["is_eligible_for_trend"] is True

# 10. Coverage below 95% is excluded from primary trend
def test_coverage_below_95_percent_is_excluded():
    records = []
    # 300 days out of 365 = 82.1%
    for i in range(1, 366):
        records.append({
            "date": f"2001-06-01",
            "temperature_max_original": 25.0 if i <= 300 else None
        })
    cov = DataQualityService.calculate_annual_coverage(records)
    assert cov[2001]["is_eligible_for_trend"] is False
    assert "below required 95.0%" in cov[2001]["exclusion_reason"]

# 11. No heatwaves returns empty event list and zero counts
def test_no_heatwaves_returns_zero_counts():
    threshold = 40.0
    records = [
        {"date": "2000-06-01", "temperature_max_original": 25.0},
        {"date": "2000-06-02", "temperature_max_original": 26.0},
    ]
    events, stats = HazardDetector.detect_heatwaves(records, threshold)
    assert len(events) == 0
    assert stats[2000]["event_count"] == 0

# 12. Zero starting count does not produce invalid percentage change
def test_zero_starting_count_percentage_change():
    metrics = [
        AnnualMetric(
            year=1990, event_count=0, heatwave_days=0, mean_duration=0.0, max_duration=0,
            data_coverage_pct=99.0, expected_days=365, valid_original_days=360,
            imputed_days=0, missing_days=5, is_eligible_for_trend=True
        ),
        AnnualMetric(
            year=1991, event_count=3, heatwave_days=10, mean_duration=3.3, max_duration=4,
            data_coverage_pct=99.0, expected_days=365, valid_original_days=360,
            imputed_days=0, missing_days=5, is_eligible_for_trend=True
        )
    ]
    trend = TrendAnalyzer.calculate_trend_and_rolling(metrics)
    assert trend.percentage_change is None
    assert "percentage change is undefined" in trend.percentage_change_note
    assert trend.slope > 0

# 13. Mode-first with median fallback imputation test
def test_mode_first_median_fallback_imputation():
    # Window of valid originals around missing index: [30.0, 30.0, 30.0, 32.0, 33.0]
    # Unique mode is 30.0
    raw = [
        {"date": "2000-01-01", "temperature_max_original": 30.0},
        {"date": "2000-01-02", "temperature_max_original": 30.0},
        {"date": "2000-01-03", "temperature_max_original": 30.0},
        {"date": "2000-01-04", "temperature_max_original": None}, # missing date
        {"date": "2000-01-05", "temperature_max_original": 32.0},
        {"date": "2000-01-06", "temperature_max_original": 33.0},
    ]
    cleaned, summary = DataQualityService.clean_and_impute(raw, "2000-01-01", "2000-01-06", "test_reg")
    missing_rec = cleaned[3]
    assert missing_rec["is_imputed"] is True
    assert missing_rec["imputation_method"] == "mode"
    assert missing_rec["temperature_max_imputed"] == 30.0
