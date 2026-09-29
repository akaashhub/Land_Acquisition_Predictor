import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, riskBg } from '../services/api';

export default function RiskMonitor() {
  const [high, setHigh] = useState<any[]>([]);
  const [crit, setCrit] = useState<any[]>([]);

  useEffect(() => {
    Promise.all([
      api.projects({ risk: 'HIGH', limit: 30, sort_by: 'risk_score' }),
      api.projects({ risk: 'CRITICAL', limit: 30, sort_by: 'risk_score' }),
    ]).then(([h, c]) => { setHigh(h.items); setCrit(c.items); });
  }, []);

  const Table = ({ items }: { items: any[] }) => (
    <table className="w-full text-sm">
      <thead className="bg-slate-50 text-xs uppercase text-slate-500">
        <tr>
          <th className="text-left px-3 py-2">Project</th>
          <th className="text-left px-3 py-2">Location</th>
          <th className="text-left px-3 py-2">Risk</th>
          <th className="text-left px-3 py-2">Bottleneck</th>
          <th className="text-left px-3 py-2">Est. Delay</th>
        </tr>
      </thead>
      <tbody>
        {items.map(p => (
          <tr key={p.project_id} className="border-t border-slate-100 hover:bg-slate-50">
            <td className="px-3 py-2">
              <Link to={`/projects/${p.project_id}`} className="text-blue-700 font-medium hover:underline">{p.project_id}</Link>
              <div className="text-xs text-slate-500 truncate max-w-[220px]">{p.project_name}</div>
            </td>
            <td className="px-3 py-2 text-xs">{p.district}, {p.state}</td>
            <td className="px-3 py-2">
              <span className={`px-2 py-0.5 rounded border text-xs font-semibold ${riskBg(p.risk_category)}`}>
                {p.risk_score} {p.risk_category}
              </span>
            </td>
            <td className="px-3 py-2 text-xs">{p.bottleneck_stage || '—'}</td>
            <td className="px-3 py-2">{p.estimated_delay_days != null ? `${Math.round(p.estimated_delay_days)}d` : '—'}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-slate-800">Risk Monitor</h1>
      <div className="bg-white border border-red-200 rounded-lg shadow-sm overflow-hidden">
        <div className="px-4 py-3 bg-red-50 border-b border-red-100 font-semibold text-red-800 text-sm">
          CRITICAL ({crit.length})
        </div>
        <Table items={crit} />
      </div>
      <div className="bg-white border border-orange-200 rounded-lg shadow-sm overflow-hidden">
        <div className="px-4 py-3 bg-orange-50 border-b border-orange-100 font-semibold text-orange-800 text-sm">
          HIGH ({high.length})
        </div>
        <Table items={high} />
      </div>
    </div>
  );
}
