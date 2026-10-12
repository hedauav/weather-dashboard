import numpy as np
from datetime import datetime, date
from typing import List, Dict, Any, Tuple
from app.config import settings

class HazardDetector:
    @staticmethod
    def calculate_baseline_threshold(
        baseline_records: List[Dict[str, Any]],
        percentile: float = 95.0
    ) -> float:
        """
        Calculates fixed regional 95th-percentile threshold T95
        during the baseline period (1991-2020) from valid original observations only.
        """
        valid_temps = [
            r["temperature_max_original"]
            for r in baseline_records
            if r.get("temperature_max_original") is not None
        ]
        if len(valid_temps) < 365 * 10:  # Need at least 10 years of data in baseline
            raise ValueError(f"Insufficient baseline data: only {len(valid_temps)} valid days found.")
        
        t95 = float(np.percentile(valid_temps, percentile))
        return round(t95, 2)

    @classmethod
    def detect_heatwaves(
        cls,
        records: List[Dict[str, Any]],
        threshold: float,
        min_consecutive_days: int = 3
    ) -> Tuple[List[Dict[str, Any]], Dict[int, Dict[str, Any]]]:
        """
        Operational Heatwave Definition (PRD 7.2):
        Run of >= 3 consecutive calendar days where original valid Tmax > threshold.
        Safety Rule: Imputed temperatures CANNOT qualify or bridge a day.
        Missing date or missing temperature breaks the sequence.
        
        Returns:
        1. List of individual events with start, end, duration, max_temp, excess_temp
        2. Annual metrics with event counts, heatwave days, mean duration, max duration
        """
        events = []
        current_streak = []
        event_counter = 1

        for r in records:
            orig = r.get("temperature_max_original")
            # Strict condition: MUST be valid original and strictly greater than threshold
            if orig is not None and orig > threshold:
                current_streak.append(r)
            else:
                # Sequence broken by valid temp <= threshold OR missing/imputed day
                if len(current_streak) >= min_consecutive_days:
                    events.append(cls._build_event(current_streak, threshold, event_counter))
                    event_counter += 1
                current_streak = []

        # Flush any open sequence at the end of the records
        if len(current_streak) >= min_consecutive_days:
            events.append(cls._build_event(current_streak, threshold, event_counter))

        # Attribution to years (PRD 7.5):
        # Event crossing Dec 31: Count as 1 event in total event list.
        # Days are allocated to respective calendar years.
        # Event count is attributed to the start year of the event to avoid double-counting.
        annual_heatwave_stats = cls._aggregate_annual_hazard(events, records)
        return events, annual_heatwave_stats

    @staticmethod
    def _build_event(streak: List[Dict[str, Any]], threshold: float, index: int) -> Dict[str, Any]:
        start_d = datetime.strptime(streak[0]["date"], "%Y-%m-%d").date()
        end_d = datetime.strptime(streak[-1]["date"], "%Y-%m-%d").date()
        duration = len(streak)
        max_t = max(r["temperature_max_original"] for r in streak)
        excess_t = round(max_t - threshold, 2)
        
        # Determine all years crossed by this event
        crossing_years = sorted(list({int(r["date"][:4]) for r in streak}))
        
        return {
            "event_id": f"hw_evt_{index}_{start_d.strftime('%Y%m%d')}",
            "start_date": start_d,
            "end_date": end_d,
            "duration_days": duration,
            "max_temperature": round(max_t, 2),
            "threshold": threshold,
            "excess_temperature": excess_t,
            "crossing_years": crossing_years,
            "status": "confirmed"
        }

    @staticmethod
    def _aggregate_annual_hazard(
        events: List[Dict[str, Any]],
        all_records: List[Dict[str, Any]]
    ) -> Dict[int, Dict[str, Any]]:
        # Map all analysis years
        years = sorted(list({int(r["date"][:4]) for r in all_records}))
        stats = {
            yr: {
                "event_count": 0,
                "heatwave_days": 0,
                "durations": []
            }
            for yr in years
        }

        # 1. Attribute qualifying days to each year
        for evt in events:
            # Attribute event count to its start year
            start_yr = evt["start_date"].year
            if start_yr in stats:
                stats[start_yr]["event_count"] += 1
                stats[start_yr]["durations"].append(evt["duration_days"])

        # Count heatwave days per year
        # A day is a heatwave day if it is part of a confirmed event
        confirmed_hw_dates = set()
        for evt in events:
            cur = evt["start_date"]
            end = evt["end_date"]
            from datetime import timedelta
            while cur <= end:
                confirmed_hw_dates.add(cur.strftime("%Y-%m-%d"))
                cur += timedelta(days=1)

        for r in all_records:
            if r["date"] in confirmed_hw_dates:
                yr = int(r["date"][:4])
                if yr in stats:
                    stats[yr]["heatwave_days"] += 1

        annual_summary = {}
        for yr, data in stats.items():
            durations = data["durations"]
            mean_dur = float(np.mean(durations)) if durations else 0.0
            max_dur = int(np.max(durations)) if durations else 0
            
            annual_summary[yr] = {
                "year": yr,
                "event_count": data["event_count"],
                "heatwave_days": data["heatwave_days"],
                "mean_duration": round(mean_dur, 1),
                "max_duration": max_dur
            }

        return annual_summary
