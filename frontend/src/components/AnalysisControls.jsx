import React, { useState } from 'react';
import { MapPin, Calendar, Play, Layers, Compass, AlertCircle } from 'lucide-react';

export default function AnalysisControls({
  presets,
  regionType,
  setRegionType,
  selectedPreset,
  setSelectedPreset,
  customCoords,
  setCustomCoords,
  bboxCoords,
  setBboxCoords,
  startDate,
  setStartDate,
  endDate,
  setEndDate,
  hazardType,
  loading,
  onAnalyze,
  error
}) {
  return (
    <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px' }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        
        {/* Top Row: Region Selector Tabs & Hazard selector */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
          <div>
            <label style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700, letterSpacing: '0.05em', marginBottom: '8px', display: 'block' }}>
              1. Geographic Region Mode
            </label>
            <div style={{ display: 'inline-flex', background: 'var(--bg-tertiary)', padding: '4px', borderRadius: 'var(--radius-md)' }}>
              {[
                { id: 'city', label: 'City' },
                { id: 'state', label: 'State' },
                { id: 'custom_bbox', label: 'Custom Bounding Box' }
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setRegionType(tab.id)}
                  style={{
                    background: regionType === tab.id ? 'var(--bg-secondary)' : 'transparent',
                    color: regionType === tab.id ? 'var(--text-main)' : 'var(--text-muted)',
                    border: 'none',
                    padding: '8px 16px',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '0.85rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    boxShadow: regionType === tab.id ? '0 2px 8px rgba(0,0,0,0.4)' : 'none'
                  }}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700, letterSpacing: '0.05em', marginBottom: '8px', display: 'block' }}>
              Hazard Type (PRD Default)
            </label>
            <select
              value={hazardType}
              disabled
              style={{
                cursor: 'not-allowed',
                background: 'rgba(239, 68, 68, 0.1)',
                color: '#f87171',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                fontWeight: 600,
                padding: '8px 14px'
              }}
            >
              <option value="heatwave">🔥 Heatwave (Active)</option>
              <option value="drought">💧 Drought (Out of scope)</option>
              <option value="wildfire">🌲 Wildfire (Out of scope)</option>
            </select>
          </div>
        </div>

        {/* Middle Row: Region Input Parameters */}
        <div style={{ background: 'rgba(0, 0, 0, 0.2)', padding: '16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
          {regionType === 'city' && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', alignItems: 'center' }}>
              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px', display: 'block' }}>
                  Select Preset City
                </label>
                <select
                  value={selectedPreset}
                  onChange={(e) => setSelectedPreset(e.target.value)}
                  style={{ width: '100%' }}
                >
                  <option value="">-- Choose Preset or Enter Coords below --</option>
                  {presets.cities?.map(c => (
                    <option key={c.id} value={c.id}>{c.name} ({c.lat}, {c.lon})</option>
                  ))}
                </select>
              </div>
              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px', display: 'block' }}>
                  Or Custom Latitude (-90 to 90)
                </label>
                <input
                  type="number"
                  step="0.0001"
                  placeholder="e.g. 28.6139"
                  value={customCoords.lat}
                  onChange={(e) => setCustomCoords({ ...customCoords, lat: e.target.value })}
                  style={{ width: '100%' }}
                />
              </div>
              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px', display: 'block' }}>
                  Custom Longitude (-180 to 180)
                </label>
                <input
                  type="number"
                  step="0.0001"
                  placeholder="e.g. 77.2090"
                  value={customCoords.lon}
                  onChange={(e) => setCustomCoords({ ...customCoords, lon: e.target.value })}
                  style={{ width: '100%' }}
                />
              </div>
            </div>
          )}

          {regionType === 'state' && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', alignItems: 'center' }}>
              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px', display: 'block' }}>
                  Select Preset State
                </label>
                <select
                  value={selectedPreset}
                  onChange={(e) => setSelectedPreset(e.target.value)}
                  style={{ width: '100%' }}
                >
                  <option value="">-- Choose State Centroid --</option>
                  {presets.states?.map(s => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px', display: 'block' }}>
                  Centroid Latitude
                </label>
                <input
                  type="number"
                  step="0.0001"
                  placeholder="e.g. 27.0238"
                  value={customCoords.lat}
                  onChange={(e) => setCustomCoords({ ...customCoords, lat: e.target.value })}
                  style={{ width: '100%' }}
                />
              </div>
              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px', display: 'block' }}>
                  Centroid Longitude
                </label>
                <input
                  type="number"
                  step="0.0001"
                  placeholder="e.g. 74.2179"
                  value={customCoords.lon}
                  onChange={(e) => setCustomCoords({ ...customCoords, lon: e.target.value })}
                  style={{ width: '100%' }}
                />
              </div>
            </div>
          )}

          {regionType === 'custom_bbox' && (
            <div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px', display: 'block' }}>Min Lat</label>
                  <input
                    type="number"
                    step="0.01"
                    placeholder="26.0"
                    value={bboxCoords.min_lat}
                    onChange={(e) => setBboxCoords({ ...bboxCoords, min_lat: e.target.value })}
                    style={{ width: '100%' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px', display: 'block' }}>Max Lat</label>
                  <input
                    type="number"
                    step="0.01"
                    placeholder="30.0"
                    value={bboxCoords.max_lat}
                    onChange={(e) => setBboxCoords({ ...bboxCoords, max_lat: e.target.value })}
                    style={{ width: '100%' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px', display: 'block' }}>Min Lon</label>
                  <input
                    type="number"
                    step="0.01"
                    placeholder="75.0"
                    value={bboxCoords.min_lon}
                    onChange={(e) => setBboxCoords({ ...bboxCoords, min_lon: e.target.value })}
                    style={{ width: '100%' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px', display: 'block' }}>Max Lon</label>
                  <input
                    type="number"
                    step="0.01"
                    placeholder="79.0"
                    value={bboxCoords.max_lon}
                    onChange={(e) => setBboxCoords({ ...bboxCoords, max_lon: e.target.value })}
                    style={{ width: '100%' }}
                  />
                </div>
              </div>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '8px' }}>
                Bounding box is validated (max 10° span). Central representative grid point sampled for historical ERA5 retrieval.
              </p>
            </div>
          )}
        </div>

        {/* Bottom Row: Date Range and Execute Analysis */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: '16px' }}>
          <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Calendar size={13} /> Start Date (Default 1990)
              </label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                min="1950-01-01"
                max={endDate}
              />
            </div>
            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Calendar size={13} /> End Date (Default 2020)
              </label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                min={startDate}
                max={new Date().toISOString().split('T')[0]}
              />
            </div>
          </div>

          <button
            className="btn-primary"
            onClick={onAnalyze}
            disabled={loading}
            style={{ padding: '12px 28px', fontSize: '1rem' }}
          >
            {loading ? (
              <>
                <span className="spinner" style={{ display: 'inline-block', width: '16px', height: '16px', border: '2px solid #fff', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
                Computing ERA5 Heatwaves...
              </>
            ) : (
              <>
                <Play size={18} fill="#ffffff" /> Run Hazard Analysis
              </>
            )}
          </button>
        </div>

        {error && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: 'var(--radius-md)',
            padding: '12px 16px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            color: '#f87171',
            fontSize: '0.875rem'
          }}>
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

      </div>
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
