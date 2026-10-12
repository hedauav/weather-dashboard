const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1';

export async function fetchPresets() {
  const res = await fetch(`${API_BASE}/regions/presets`);
  if (!res.ok) throw new Error('Failed to fetch regional presets');
  return res.json();
}

export async function resolveRegion(payload) {
  const res = await fetch(`${API_BASE}/regions/resolve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to resolve region coordinates');
  }
  return res.json();
}

export async function runHazardAnalysis(payload) {
  console.log('[Climate API] Sending REAL fetch request to backend:', `${API_BASE}/analysis`, payload);
  const res = await fetch(`${API_BASE}/analysis`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Analysis calculation failed');
  }
  return res.json();
}

export async function fetchAnalysisById(analysisId) {
  const res = await fetch(`${API_BASE}/analysis/${analysisId}`);
  if (!res.ok) throw new Error('Failed to retrieve cached analysis');
  return res.json();
}
