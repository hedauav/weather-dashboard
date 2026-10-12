import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import AnalysisControls from './components/AnalysisControls';
import SummaryCards from './components/SummaryCards';
import TrendCharts from './components/TrendCharts';
import EventTable from './components/EventTable';
import QualityPanel from './components/QualityPanel';
import InteractiveMap from './components/InteractiveMap';
import { fetchPresets, runHazardAnalysis } from './services/api';

export default function App() {
  const [presets, setPresets] = useState({ cities: [], states: [] });
  const [regionType, setRegionType] = useState('city');
  const [selectedPreset, setSelectedPreset] = useState('delhi');
  const [customCoords, setCustomCoords] = useState({ lat: '', lon: '' });
  const [bboxCoords, setBboxCoords] = useState({ min_lat: '26.0', max_lat: '30.0', min_lon: '75.0', max_lon: '79.0' });
  const [startDate, setStartDate] = useState('1990-01-01');
  const [endDate, setEndDate] = useState('2020-12-31');
  const [hazardType] = useState('heatwave');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [analysisData, setAnalysisData] = useState(null);

  useEffect(() => {
    fetchPresets()
      .then(data => {
        setPresets(data);
      })
      .catch(err => {
        console.warn('Could not load presets:', err);
      });
  }, []);

  const handleAnalyze = async () => {
    setError(null);
    setLoading(true);

    try {
      const payload = {
        region_type: regionType,
        hazard_type: hazardType,
        start_date: startDate,
        end_date: endDate
      };

      if (regionType === 'city' || regionType === 'state') {
        if (customCoords.lat && customCoords.lon) {
          payload.latitude = parseFloat(customCoords.lat);
          payload.longitude = parseFloat(customCoords.lon);
          payload.name = `${regionType.toUpperCase()} (${customCoords.lat}, ${customCoords.lon})`;
        } else if (selectedPreset) {
          payload.name = selectedPreset;
        } else {
          throw new Error('Please select a preset or provide custom latitude/longitude coordinates.');
        }
      } else if (regionType === 'custom_bbox') {
        payload.bounding_box = {
          min_lat: parseFloat(bboxCoords.min_lat),
          max_lat: parseFloat(bboxCoords.max_lat),
          min_lon: parseFloat(bboxCoords.min_lon),
          max_lon: parseFloat(bboxCoords.max_lon)
        };
      }

      const res = await runHazardAnalysis(payload);
      setAnalysisData(res);
    } catch (err) {
      setError(err.message || 'An error occurred during analysis');
    } finally {
      setLoading(false);
    }
  };

  // Run initial analysis automatically on mount (Delhi 1990-2020)
  useEffect(() => {
    handleAnalyze();
  }, []);

  return (
    <div style={{ maxWidth: '1440px', margin: '0 auto', padding: '24px 20px 60px' }}>
      <Header />

      <AnalysisControls
        presets={presets}
        regionType={regionType}
        setRegionType={setRegionType}
        selectedPreset={selectedPreset}
        setSelectedPreset={setSelectedPreset}
        customCoords={customCoords}
        setCustomCoords={setCustomCoords}
        bboxCoords={bboxCoords}
        setBboxCoords={setBboxCoords}
        startDate={startDate}
        setStartDate={setStartDate}
        endDate={endDate}
        setEndDate={setEndDate}
        hazardType={hazardType}
        loading={loading}
        onAnalyze={handleAnalyze}
        error={error}
      />

      {analysisData && (
        <>
          <SummaryCards data={analysisData} />

          <InteractiveMap
            region={analysisData.region}
            threshold={analysisData.temperature_threshold_celsius}
            eventCount={analysisData.events?.length || 0}
          />

          <TrendCharts
            annualMetrics={analysisData.annual_metrics}
            trendMetrics={analysisData.trend_metrics}
          />

          <QualityPanel
            qualitySummary={analysisData.quality_summary}
            insights={analysisData.summary_insights}
            region={analysisData.region}
            baselineMetadata={analysisData.baseline_metadata}
          />

          <EventTable
            events={analysisData.events}
            threshold={analysisData.temperature_threshold_celsius}
          />
        </>
      )}

      {/* Footer */}
      <footer style={{
        marginTop: '40px',
        textAlign: 'center',
        padding: '20px',
        borderTop: '1px solid var(--border-subtle)',
        color: 'var(--text-dim)',
        fontSize: '0.8rem'
      }}>
        Climate Hazard Trend Analyzer &copy; Dygnify Ventures Case Study &bull; ERA5 Historical Reanalysis via Open-Meteo &bull; Operational rule: ≥3 consecutive days &gt; pooled 1991–2020 T95 threshold.
      </footer>
    </div>
  );
}
