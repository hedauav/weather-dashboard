import React from 'react';
import { MapContainer, TileLayer, Marker, Popup, Rectangle } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { MapPin } from 'lucide-react';

// Fix Leaflet marker icons in Vite/React bundling
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

export default function InteractiveMap({ region, threshold, eventCount }) {
  if (!region) return null;

  const lat = region.latitude || 28.6139;
  const lon = region.longitude || 77.2090;
  const bbox = region.bounding_box;

  return (
    <div className="glass-panel" style={{ padding: '20px', marginBottom: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
        <div>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <MapPin size={16} color="var(--accent-flame)" /> Regional Grid Spatial Footprint
          </h3>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Representative ERA5 reanalysis sampling coordinates ({lat.toFixed(4)}, {lon.toFixed(4)})
          </p>
        </div>
        <span className="badge badge-heatwave">
          {eventCount} Events Verified
        </span>
      </div>

      <div style={{ height: '240px', width: '100%', borderRadius: 'var(--radius-md)', overflow: 'hidden' }}>
        <MapContainer
          key={`${lat}-${lon}`}
          center={[lat, lon]}
          zoom={region.region_type === 'custom_bbox' ? 6 : 8}
          scrollWheelZoom={false}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://carto.com/">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          />
          <Marker position={[lat, lon]}>
            <Popup>
              <strong>{region.name}</strong><br />
              Threshold: {threshold?.toFixed(1)}°C<br />
              {region.spatial_disclosure}
            </Popup>
          </Marker>

          {bbox && (
            <Rectangle
              bounds={[
                [bbox.min_lat, bbox.min_lon],
                [bbox.max_lat, bbox.max_lon]
              ]}
              pathOptions={{ color: '#ff5722', weight: 2, fillOpacity: 0.2 }}
            />
          )}
        </MapContainer>
      </div>
    </div>
  );
}
