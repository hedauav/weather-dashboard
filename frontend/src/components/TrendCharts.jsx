import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Bar, Line } from 'react-chartjs-2';
import { TrendingUp, BarChart3, AlertTriangle } from 'lucide-react';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

export default function TrendCharts({ annualMetrics, trendMetrics }) {
  if (!annualMetrics || annualMetrics.length === 0) return null;

  const years = annualMetrics.map(m => m.year);
  const eventCounts = annualMetrics.map(m => m.event_count);
  const heatwaveDays = annualMetrics.map(m => m.heatwave_days);
  const rollingAverages = years.map(y => trendMetrics?.rolling_average_5yr?.[y] ?? null);

  // Excluded year flags for tooltips/indicators
  const excludedSet = new Set(trendMetrics?.excluded_years || []);

  // Chart 1: Heatwave Events & 5-Year Rolling Average (Combined Bar + Line)
  const eventsChartData = {
    labels: years,
    datasets: [
      {
        type: 'line',
        label: '5-Year Rolling Average',
        data: rollingAverages,
        borderColor: '#f59e0b',
        backgroundColor: 'rgba(245, 158, 11, 0.1)',
        borderWidth: 3,
        pointRadius: 2,
        tension: 0.35,
        yAxisID: 'y'
      },
      {
        type: 'bar',
        label: 'Annual Confirmed Heatwave Events',
        data: eventCounts,
        backgroundColor: years.map(y => excludedSet.has(y) ? 'rgba(107, 114, 128, 0.4)' : 'rgba(255, 87, 34, 0.7)'),
        borderColor: years.map(y => excludedSet.has(y) ? '#6b7280' : '#ff5722'),
        borderWidth: 1,
        borderRadius: 4,
        yAxisID: 'y'
      }
    ]
  };

  const eventsOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          color: '#d1d5db',
          font: { family: "'Plus Jakarta Sans', sans-serif", size: 12 }
        }
      },
      tooltip: {
        callbacks: {
          afterLabel: function(context) {
            const yr = Number(context.label);
            if (excludedSet.has(yr)) {
              return '⚠️ Excluded from linear regression (<95% coverage)';
            }
            return '';
          }
        }
      }
    },
    scales: {
      x: {
        ticks: { color: '#9ca3af', maxRotation: 45 },
        grid: { color: 'rgba(255, 255, 255, 0.05)' }
      },
      y: {
        ticks: { color: '#9ca3af', stepSize: 1 },
        grid: { color: 'rgba(255, 255, 255, 0.05)' },
        title: { display: true, text: 'Number of Events', color: '#9ca3af' }
      }
    }
  };

  // Chart 2: Annual Heatwave Days
  const daysChartData = {
    labels: years,
    datasets: [
      {
        label: 'Annual Heatwave Days (≥3-day runs)',
        data: heatwaveDays,
        borderColor: '#14b8a6',
        backgroundColor: 'rgba(20, 184, 166, 0.15)',
        borderWidth: 2,
        pointBackgroundColor: '#14b8a6',
        pointRadius: 3,
        fill: true,
        tension: 0.2
      }
    ]
  };

  const daysOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          color: '#d1d5db',
          font: { family: "'Plus Jakarta Sans', sans-serif", size: 12 }
        }
      }
    },
    scales: {
      x: {
        ticks: { color: '#9ca3af', maxRotation: 45 },
        grid: { color: 'rgba(255, 255, 255, 0.05)' }
      },
      y: {
        ticks: { color: '#9ca3af' },
        grid: { color: 'rgba(255, 255, 255, 0.05)' },
        title: { display: true, text: 'Cumulative Days / Year', color: '#9ca3af' }
      }
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', gap: '20px', marginBottom: '24px' }}>
      
      {/* Chart 1 */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <TrendingUp size={18} color="var(--accent-flame)" /> Annual Heatwave Frequency & Rolling Trend
            </h3>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              Linear Regression slope: {trendMetrics?.slope > 0 ? '+' : ''}{trendMetrics?.slope?.toFixed(3)} events/year
            </p>
          </div>
          {excludedSet.size > 0 && (
            <span style={{ fontSize: '0.72rem', color: '#fbbf24', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <AlertTriangle size={13} /> {excludedSet.size} yr excluded
            </span>
          )}
        </div>
        <div style={{ height: '300px' }}>
          <Bar data={eventsChartData} options={eventsOptions} />
        </div>
      </div>

      {/* Chart 2 */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ marginBottom: '16px' }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <BarChart3 size={18} color="var(--accent-teal)" /> Annual Cumulative Heatwave Days
          </h3>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            Total days belonging to confirmed runs exceeding baseline 95th percentile
          </p>
        </div>
        <div style={{ height: '300px' }}>
          <Line data={daysChartData} options={daysOptions} />
        </div>
      </div>

    </div>
  );
}
