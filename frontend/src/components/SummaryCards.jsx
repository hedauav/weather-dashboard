import React from 'react';
import { Flame, Calendar, TrendingUp, Thermometer, ShieldCheck, Clock } from 'lucide-react';

export default function SummaryCards({ data }) {
  if (!data) return null;

  const totalEvents = data.events?.length || 0;
  const totalHeatwaveDays = data.annual_metrics?.reduce((acc, m) => acc + m.heatwave_days, 0) || 0;
  const longestDuration = data.events?.length > 0 
    ? Math.max(...data.events.map(e => e.duration_days)) 
    : 0;
  const threshold = data.temperature_threshold_celsius;
  const slope = data.trend_metrics?.slope ?? 0;
  const eligibleYears = data.trend_metrics?.eligible_years ?? 0;
  const totalYears = data.trend_metrics?.total_years ?? 0;

  const cards = [
    {
      title: 'Confirmed Heatwave Events',
      value: totalEvents,
      subtitle: `${data.requested_period.start_date.slice(0,4)}–${data.requested_period.end_date.slice(0,4)} timeline`,
      icon: Flame,
      color: '#ff5722',
      glow: 'rgba(255, 87, 34, 0.2)'
    },
    {
      title: 'Total Heatwave Days',
      value: totalHeatwaveDays,
      subtitle: 'Days meeting ≥3 consecutive day rule',
      icon: Calendar,
      color: '#f59e0b',
      glow: 'rgba(245, 158, 11, 0.2)'
    },
    {
      title: 'Longest Event Duration',
      value: `${longestDuration} Days`,
      subtitle: 'Max single persistent heat spell',
      icon: Clock,
      color: '#ef4444',
      glow: 'rgba(239, 68, 68, 0.2)'
    },
    {
      title: 'Fixed Regional Threshold (T95)',
      value: `${threshold.toFixed(1)}°C`,
      subtitle: '1991–2020 ERA5 95th Percentile',
      icon: Thermometer,
      color: '#14b8a6',
      glow: 'rgba(20, 184, 166, 0.2)'
    },
    {
      title: 'Regression Slope (Trend)',
      value: `${slope > 0 ? '+' : ''}${slope.toFixed(3)}/yr`,
      subtitle: `${(slope * 10).toFixed(2)} events / decade`,
      icon: TrendingUp,
      color: slope > 0 ? '#ff5722' : '#14b8a6',
      glow: 'rgba(255, 87, 34, 0.2)'
    },
    {
      title: 'Eligible Analysis Years',
      value: `${eligibleYears} / ${totalYears}`,
      subtitle: 'Met ≥95% data coverage standard',
      icon: ShieldCheck,
      color: '#6366f1',
      glow: 'rgba(99, 102, 241, 0.2)'
    }
  ];

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
      gap: '16px',
      marginBottom: '24px'
    }}>
      {cards.map((c, i) => {
        const IconComponent = c.icon;
        return (
          <div
            key={i}
            className="glass-panel"
            style={{
              padding: '20px',
              position: 'relative',
              overflow: 'hidden'
            }}
          >
            <div style={{
              position: 'absolute',
              top: '-15px',
              right: '-15px',
              width: '80px',
              height: '80px',
              borderRadius: '50%',
              background: c.glow,
              filter: 'blur(20px)',
              pointerEvents: 'none'
            }} />

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>
                {c.title}
              </span>
              <div style={{
                background: 'rgba(255, 255, 255, 0.05)',
                padding: '8px',
                borderRadius: 'var(--radius-sm)',
                color: c.color
              }}>
                <IconComponent size={20} />
              </div>
            </div>

            <div style={{ fontSize: '1.85rem', fontWeight: 800, letterSpacing: '-0.02em', color: '#ffffff', marginBottom: '4px' }}>
              {c.value}
            </div>

            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
              {c.subtitle}
            </div>
          </div>
        );
      })}
    </div>
  );
}
