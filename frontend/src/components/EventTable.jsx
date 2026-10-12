import React, { useState } from 'react';
import { Download, ListFilter, Calendar, ChevronLeft, ChevronRight } from 'lucide-react';

export default function EventTable({ events, threshold }) {
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 8;

  if (!events || events.length === 0) {
    return (
      <div className="glass-panel" style={{ padding: '32px', textAlign: 'center', marginBottom: '24px' }}>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
          No heatwave events met the ≥3 consecutive days &gt; T95 ({threshold?.toFixed(1)}°C) rule in this timeframe.
        </p>
      </div>
    );
  }

  // Export to CSV (PRD Bonus Feature)
  const exportToCSV = () => {
    const headers = ['Event ID,Start Date,End Date,Duration (Days),Max Temp (°C),Threshold (°C),Excess (°C),Status'];
    const rows = events.map(e => 
      `${e.event_id},${e.start_date},${e.end_date},${e.duration_days},${e.max_temperature},${e.threshold},${e.excess_temperature},${e.status}`
    );
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers, ...rows].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `heatwave_events_${events[0].start_date}_${events[events.length - 1].end_date}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const totalPages = Math.ceil(events.length / pageSize);
  const currentEvents = events.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  return (
    <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', marginBottom: '20px' }}>
        <div>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ListFilter size={18} color="var(--accent-amber)" /> Confirmed Heatwave Events Catalog
          </h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Showing {events.length} verified events strictly adhering to the 3-day consecutive threshold rule
          </p>
        </div>

        <button className="btn-secondary" onClick={exportToCSV}>
          <Download size={15} /> Export CSV
        </button>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)' }}>
              <th style={{ padding: '12px 14px' }}>Event ID</th>
              <th style={{ padding: '12px 14px' }}>Start Date</th>
              <th style={{ padding: '12px 14px' }}>End Date</th>
              <th style={{ padding: '12px 14px' }}>Duration</th>
              <th style={{ padding: '12px 14px' }}>Peak Temp</th>
              <th style={{ padding: '12px 14px' }}>Threshold (T95)</th>
              <th style={{ padding: '12px 14px' }}>Excess Temp</th>
              <th style={{ padding: '12px 14px' }}>Audit Status</th>
            </tr>
          </thead>
          <tbody>
            {currentEvents.map((evt, idx) => (
              <tr
                key={evt.event_id}
                style={{
                  borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                  transition: 'background 0.15s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.02)'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
              >
                <td style={{ padding: '12px 14px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                  {evt.event_id}
                </td>
                <td style={{ padding: '12px 14px', fontWeight: 600 }}>{evt.start_date}</td>
                <td style={{ padding: '12px 14px', fontWeight: 600 }}>{evt.end_date}</td>
                <td style={{ padding: '12px 14px' }}>
                  <span style={{
                    padding: '2px 8px',
                    borderRadius: '4px',
                    background: evt.duration_days >= 7 ? 'rgba(239, 68, 68, 0.2)' : 'rgba(245, 158, 11, 0.15)',
                    color: evt.duration_days >= 7 ? '#f87171' : '#fbbf24',
                    fontWeight: 700
                  }}>
                    {evt.duration_days} days
                  </span>
                </td>
                <td style={{ padding: '12px 14px', color: '#f87171', fontWeight: 700 }}>
                  {evt.max_temperature.toFixed(1)}°C
                </td>
                <td style={{ padding: '12px 14px', color: 'var(--text-muted)' }}>
                  {evt.threshold.toFixed(1)}°C
                </td>
                <td style={{ padding: '12px 14px', color: '#fb923c' }}>
                  +{evt.excess_temperature.toFixed(1)}°C
                </td>
                <td style={{ padding: '12px 14px' }}>
                  <span className="badge badge-success">
                    {evt.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px', paddingTop: '16px', borderTop: '1px solid var(--border-subtle)' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Page {currentPage} of {totalPages}
          </span>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              className="btn-secondary"
              disabled={currentPage === 1}
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              style={{ opacity: currentPage === 1 ? 0.5 : 1 }}
            >
              <ChevronLeft size={16} /> Prev
            </button>
            <button
              className="btn-secondary"
              disabled={currentPage === totalPages}
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              style={{ opacity: currentPage === totalPages ? 0.5 : 1 }}
            >
              Next <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
