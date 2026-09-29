import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { api, riskColor } from '../services/api';

export default function MapPage() {
  const [items, setItems] = useState<any[]>([]);
  const [filter, setFilter] = useState('');

  useEffect(() => {
    api.mapData().then(r => setItems(r.items || []));
  }, []);

  const filtered = filter ? items.filter(i => i.risk_category === filter) : items;

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center flex-wrap gap-2">
        <h1 className="text-2xl font-semibold text-slate-800">Geospatial Risk Map</h1>
        <div className="flex gap-2 text-xs">
          {['', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map(r => (
            <button key={r || 'all'} onClick={() => setFilter(r)}
              className={`px-2 py-1 rounded border ${filter === r ? 'bg-slate-800 text-white' : 'bg-white'}`}>
              {r || 'All'}
            </button>
          ))}
        </div>
      </div>
      <div className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm" style={{ height: 520 }}>
        <MapContainer center={[22.5, 79]} zoom={5} style={{ height: '100%', width: '100%' }}>
          <TileLayer attribution='&copy; OpenStreetMap' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          {filtered.map(p => (
            p.latitude && p.longitude && (
              <CircleMarker
                key={p.project_id}
                center={[p.latitude, p.longitude]}
                radius={8}
                pathOptions={{ color: riskColor(p.risk_category), fillColor: riskColor(p.risk_category), fillOpacity: 0.7 }}
              >
                <Popup>
                  <div className="text-sm">
                    <Link to={`/projects/${p.project_id}`} className="font-semibold text-blue-700">{p.project_id}</Link>
                    <div>{p.project_name}</div>
                    <div>{p.district}, {p.state}</div>
                    <div>Risk: <strong>{p.risk_score} {p.risk_category}</strong></div>
                    <div>Stage: {p.current_stage}</div>
                    <div>Bottleneck: {p.bottleneck_stage || '—'}</div>
                  </div>
                </Popup>
              </CircleMarker>
            )
          ))}
        </MapContainer>
      </div>
      <p className="text-xs text-slate-400">Green=LOW · Yellow=MEDIUM · Orange=HIGH · Red=CRITICAL · OpenStreetMap tiles</p>
    </div>
  );
}
