import React from 'react';
import { ShieldAlert, CheckCircle2, AlertTriangle, FileCode2, Info } from 'lucide-react';

export default function QualityPanel({ qualitySummary, insights, region, baselineMetadata }) {
  if (!qualitySummary) return null;

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: '20px', marginBottom: '24px' }}>
      
      {/* Evidence-Based Summary Insights */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
          <Info size={18} color="var(--accent-cyan)" /> Evidence-Based Insights
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {insights?.map((ins, idx) => (
            <div
              key={idx}
              style={{
                background: 'rgba(255, 255, 255, 0.03)',
                borderLeft: '3px solid var(--accent-amber)',
                padding: '10px 14px',
                borderRadius: '0 var(--radius-sm) var(--radius-sm) 0',
                fontSize: '0.85rem',
                lineHeight: 1.5,
                color: '#e5e7eb'
              }}
            >
              {ins}
            </div>
          ))}
        </div>

        <div style={{ marginTop: '16px', padding: '12px', background: 'rgba(20, 184, 166, 0.08)', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(20, 184, 166, 0.2)' }}>
          <p style={{ fontSize: '0.75rem', color: '#2dd4bf', lineHeight: 1.4 }}>
            <strong>Spatial Disclosure:</strong> {region?.spatial_disclosure}
          </p>
        </div>
      </div>

      {/* Data Quality & Missing-Value Audit Panel */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ShieldAlert size={18} color="var(--accent-coral)" /> Data Reliability & Audit Log
          </h3>
          <span className="badge badge-success">
            {qualitySummary.overall_coverage_pct}% Valid
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px', marginBottom: '16px' }}>
          <div style={{ background: 'rgba(0, 0, 0, 0.25)', padding: '10px', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Expected Days</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 700 }}>{qualitySummary.total_expected_days}</div>
          </div>
          <div style={{ background: 'rgba(0, 0, 0, 0.25)', padding: '10px', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Original Valid Days</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#2dd4bf' }}>{qualitySummary.total_valid_original_days}</div>
          </div>
          <div style={{ background: 'rgba(0, 0, 0, 0.25)', padding: '10px', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Imputed Values</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fbbf24' }}>{qualitySummary.total_imputed_days}</div>
          </div>
          <div style={{ background: 'rgba(0, 0, 0, 0.25)', padding: '10px', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Missing Dates</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f87171' }}>{qualitySummary.total_missing_dates}</div>
          </div>
        </div>

        <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: 1.4, marginBottom: '12px' }}>
          <strong>PRD Safety Rule:</strong> Mode-first imputed values are quarantined for secondary trend display and cannot confirm a heatwave or bridge a missing day.
        </div>

        {qualitySummary.critical_event_gap_warnings?.length > 0 ? (
          <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.25)', padding: '10px', borderRadius: 'var(--radius-sm)' }}>
            {qualitySummary.critical_event_gap_warnings.map((w, idx) => (
              <div key={idx} style={{ fontSize: '0.75rem', color: '#f87171', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <AlertTriangle size={14} /> {w}
              </div>
            ))}
          </div>
        ) : (
          <div style={{ background: 'rgba(20, 184, 166, 0.08)', border: '1px solid rgba(20, 184, 166, 0.2)', padding: '10px', borderRadius: 'var(--radius-sm)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <CheckCircle2 size={15} color="#2dd4bf" />
            <span style={{ fontSize: '0.75rem', color: '#2dd4bf' }}>No critical missing streaks detected that would compromise confirmed events.</span>
          </div>
        )}
      </div>

    </div>
  );
}
