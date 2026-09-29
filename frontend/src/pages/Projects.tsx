import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, riskBg } from '../services/api';

export default function Projects() {
  const [items, setItems] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [filters, setFilters] = useState({ search: '', risk: '', state: '', sort_by: 'risk_score' });

  useEffect(() => {
    api.projects({ ...filters, limit: 50 }).then(r => {
      setItems(r.items); setTotal(r.total);
    });
  }, [filters]);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold text-slate-800">Projects</h1>
      <div className="flex flex-wrap gap-2">
        <input
          className="border border-slate-300 rounded px-3 py-1.5 text-sm"
          placeholder="Search ID or name…"
          value={filters.search}
          onChange={e => setFilters({ ...filters, search: e.target.value })}
        />
        <select className="border border-slate-300 rounded px-2 py-1.5 text-sm" value={filters.risk}
          onChange={e => setFilters({ ...filters, risk: e.target.value })}>
          <option value="">All risk</option>
          {['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map(r => <option key={r} value={r}>{r}</option>)}
        </select>
        <select className="border border-slate-300 rounded px-2 py-1.5 text-sm" value={filters.sort_by}
          onChange={e => setFilters({ ...filters, sort_by: e.target.value })}>
          <option value="risk_score">Sort: Risk</option>
          <option value="delay_probability">Sort: Probability</option>
          <option value="estimated_delay_days">Sort: Est. Delay</option>
          <option value="project_name">Sort: Name</option>
        </select>
        <span className="text-sm text-slate-500 self-center">{total} projects</span>
      </div>
      <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              <th className="text-left px-3 py-2">Project</th>
              <th className="text-left px-3 py-2">State / District</th>
              <th className="text-left px-3 py-2">Stage</th>
              <th className="text-left px-3 py-2">Risk</th>
              <th className="text-left px-3 py-2">Prob.</th>
              <th className="text-left px-3 py-2">Est. Delay</th>
              <th className="text-left px-3 py-2">Primary Risk</th>
            </tr>
          </thead>
          <tbody>
            {items.map(p => (
              <tr key={p.project_id} className="border-t border-slate-100 hover:bg-slate-50">
                <td className="px-3 py-2">
                  <Link to={`/projects/${p.project_id}`} className="text-blue-700 font-medium hover:underline">{p.project_id}</Link>
                  <div className="text-xs text-slate-500 truncate max-w-[200px]">{p.project_name}</div>
                </td>
                <td className="px-3 py-2 text-xs">{p.district}<br/>{p.state}</td>
                <td className="px-3 py-2 text-xs">{p.current_stage}</td>
                <td className="px-3 py-2">
                  <span className={`px-2 py-0.5 rounded border text-xs font-semibold ${riskBg(p.risk_category)}`}>
                    {p.risk_score} {p.risk_category}
                  </span>
                </td>
                <td className="px-3 py-2">{p.delay_probability ?? '—'}%</td>
                <td className="px-3 py-2">{p.estimated_delay_days != null ? `${Math.round(p.estimated_delay_days)}d` : '—'}</td>
                <td className="px-3 py-2 text-xs">{p.bottleneck_stage || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
