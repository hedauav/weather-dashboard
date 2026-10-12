import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from app.schemas import AnnualMetric, TrendMetrics

class TrendAnalyzer:
    @staticmethod
    def calculate_trend_and_rolling(
        annual_metrics: List[AnnualMetric]
    ) -> TrendMetrics:
        """
        PRD 7.6 Trend Analysis:
        - Linear regression on annual confirmed heatwave counts (events per year)
        - Only eligible years meeting the coverage rule (>= 95%) enter the regression
        - Five-year rolling average across the timeline
        - Zero starting count: do not calculate invalid percentage change; show absolute counts
        - PRD 7.7: Summary insights derived dynamically from calculated data
        """
        all_years = [m.year for m in annual_metrics]
        eligible_metrics = [m for m in annual_metrics if m.is_eligible_for_trend]
        excluded_years = [m.year for m in annual_metrics if not m.is_eligible_for_trend]
        
        # 1. Linear regression on eligible years
        slope = 0.0
        percentage_change = None
        percentage_note = None

        if len(eligible_metrics) >= 2:
            x_vals = np.array([m.year for m in eligible_metrics], dtype=float)
            y_vals = np.array([m.event_count for m in eligible_metrics], dtype=float)
            
            # Simple linear regression: y = slope * x + intercept
            x_mean = np.mean(x_vals)
            y_mean = np.mean(y_vals)
            numerator = np.sum((x_vals - x_mean) * (y_vals - y_mean))
            denominator = np.sum((x_vals - x_mean) ** 2)
            
            if denominator != 0:
                slope = float(numerator / denominator)

            # First and last eligible year count comparison
            first_count = eligible_metrics[0].event_count
            last_count = eligible_metrics[-1].event_count
            
            if first_count == 0:
                percentage_change = None
                percentage_note = f"Baseline start year ({eligible_metrics[0].year}) recorded 0 heatwave events; percentage change is undefined. Absolute change is {last_count - first_count:+d} events."
            else:
                pct = ((last_count - first_count) / first_count) * 100.0
                percentage_change = round(float(pct), 1)
                percentage_note = f"Observed change from {first_count} to {last_count} events ({percentage_change:+.1f}%)."
        else:
            percentage_note = "Insufficient eligible years to compute regression slope."

        # 2. Five-year rolling average
        # Map year -> event_count for entire sequence
        df = pd.DataFrame([{"year": m.year, "count": m.event_count} for m in annual_metrics])
        df = df.sort_values("year").reset_index(drop=True)
        # 5-year rolling mean, centered or min_periods=1
        df["rolling_5yr"] = df["count"].rolling(window=5, min_periods=1, center=True).mean()
        
        rolling_map: Dict[int, Optional[float]] = {}
        for _, row in df.iterrows():
            rolling_map[int(row["year"])] = round(float(row["rolling_5yr"]), 2)

        # 3. Dynamic trend description
        if len(eligible_metrics) < 3:
            trend_desc = "The selected historical period contains insufficient eligible years (<3) for a reliable trend estimate."
        elif abs(slope) < 0.005:
            trend_desc = f"The historical trend is relatively flat with a slope of {slope:+.3f} events/year over {len(eligible_metrics)} eligible years."
        elif slope > 0:
            trend_desc = f"The fitted historical trend shows an increase of {slope:+.3f} heatwave events per year ({slope*10:+.2f} events per decade)."
        else:
            trend_desc = f"The fitted historical trend shows a decrease of {abs(slope):.3f} heatwave events per year ({slope*10:+.2f} events per decade)."

        return TrendMetrics(
            slope=round(slope, 4),
            rolling_average_5yr=rolling_map,
            total_years=len(all_years),
            eligible_years=len(eligible_metrics),
            excluded_years=excluded_years,
            trend_description=trend_desc,
            percentage_change=percentage_change,
            percentage_change_note=percentage_note
        )

    @staticmethod
    def generate_summary_insights(
        trend_metrics: TrendMetrics,
        annual_metrics: List[AnnualMetric],
        threshold: float,
        total_events: int
    ) -> List[str]:
        insights = []
        insights.append(trend_metrics.trend_description)
        
        if total_events > 0:
            # Find year with max events
            max_yr = max(annual_metrics, key=lambda m: m.event_count)
            insights.append(f"Peak heatwave activity occurred in {max_yr.year} with {max_yr.event_count} confirmed events and {max_yr.heatwave_days} qualifying days.")
            
            # Find longest duration year
            max_dur_yr = max(annual_metrics, key=lambda m: m.max_duration)
            if max_dur_yr.max_duration > 0:
                insights.append(f"The longest single heatwave reached {max_dur_yr.max_duration} consecutive days in {max_dur_yr.year}.")
        else:
            insights.append("Zero confirmed heatwave events were detected during the requested analysis window.")

        insights.append(f"Baseline (1991–2020) fixed 95th-percentile temperature threshold is {threshold:.1f}°C.")

        if trend_metrics.excluded_years:
            ex_str = ", ".join(str(y) for y in trend_metrics.excluded_years[:5])
            if len(trend_metrics.excluded_years) > 5:
                ex_str += f" (+{len(trend_metrics.excluded_years)-5} more)"
            insights.append(f"Years excluded from primary trend due to <95% coverage: {ex_str}.")
        
        if trend_metrics.percentage_change_note:
            insights.append(trend_metrics.percentage_change_note)

        return insights
