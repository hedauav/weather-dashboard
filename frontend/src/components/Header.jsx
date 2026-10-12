import React from 'react';
import { Flame, ShieldCheck, Database, Calendar } from 'lucide-react';

export default function Header() {
  return (
    <header className="glass-panel" style={{ padding: '20px 32px', marginBottom: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            background: 'linear-gradient(135deg, #ff5722 0%, #f59e0b 100%)',
            padding: '12px',
            borderRadius: '14px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 20px rgba(255, 87, 34, 0.4)'
          }}>
            <Flame size={28} color="#ffffff" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h1 style={{ fontSize: '1.5rem', fontWeight: 800, letterSpacing: '-0.02em', background: 'linear-gradient(to right, #ffffff, #d1d5db)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                Climate Hazard Trend Analyzer
              </h1>
              <span className="badge badge-heatwave">ERA5 Reanalysis</span>
            </div>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              Historical Heatwave Event Detection, Linear Regression & Reliability Auditing
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            <Database size={15} color="var(--accent-teal)" />
            <span>Baseline: <strong>1991–2020</strong></span>
          </div>
          <div style={{ width: '1px', height: '24px', background: 'var(--border-subtle)' }} />
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            <ShieldCheck size={15} color="var(--accent-amber)" />
            <span>Rule: <strong>&ge;3 Days &gt; T95</strong></span>
          </div>
        </div>
      </div>
    </header>
  );
}
