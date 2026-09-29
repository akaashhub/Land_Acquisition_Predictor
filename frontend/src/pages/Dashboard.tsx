import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, riskBg } from '../services/api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const COLORS = { LOW: '#16a34a', MEDIUM: '#ca8a04', HIGH: '#ea580c', CRITICAL: '#dc2626' };

export default function Dashboard() {
  const [ov, setOv] = useState<any>(null);
  const [dist, setDist] = useState<any>(null);
  const [stages, setStages] = useState<any[]>([]);
  const [critical, setCritical] = useState<any[]>([]);
  const [err, setErr] = useState('');

  useEffect(() => {
    Promise.all([
      api.overview(),
      api.riskDist(),
      api.stageBottlenecks(),
      api.projects({ risk: 'CRITICAL', limit: 8, sort_by: 'risk_score' }),
    ]).then(([o, d, s, p]) => {
      setOv(o); setDist(d); setStages(s.items || []); setCritical(p.items || []);
    }).catch(e => setErr(e.message));
  }, []);

  if (err) return <div className="text-red-600">Unable to load dashboard: {err}</div>;
  if (!ov) return <div className="text-slate-500">Loading analytics…</div>;

  const cards = [
    { label: 'Total Projects', value: ov.total_projects, color: 'border-slate-300' },
    { label: 'On Track (LOW)', value: ov.on_track, color: 'border-green-400' },
    { label: 'Medium Risk', value: ov.medium_risk, color: 'border-yellow-400' },
    { label: 'High Risk', value: ov.high_risk, color: 'border-orange-400' },
    { label: 'Critical Risk', value: ov.critical_risk, color: 'border-red-500' },
    { label: 'Avg Predicted Delay', value: `${ov.average_predicted_delay} days`, color: 'border-blue-400' },
  ];

  const pieData = dist ? Object.entries(dist.by_category || {}).map(([k, v]) => ({ name: k, value: v as number })) : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-800">National Overview</h1>
        <p className="text-sm text-slate-500 mt-1">{ov.disclaimer}</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {cards.map(c => (
          <div key={c.label} className={`bg-white rounded-lg border-l-4 ${c.color} shadow-sm p-4`}>
            <div className="text-xs text-slate-500 uppercase tracking-wide">{c.label}</div>
            <div className="text-2xl font-bold text-slate-800 mt-1">{c.value}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
          <h2 className="text-sm font-semibold text-slate-700 mb-3">Projects by Risk Category</h2>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                {pieData.map((e) => <Cell key={e.name} fill={COLORS[e.name as keyof typeof COLORS] || '#999'} />)}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
          <h2 className="text-sm font-semibold text-slate-700 mb-3">Stage Bottlenecks (High/Critical)</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={stages.slice(0, 6)}>
              <XAxis dataKey="stage" tick={{ fontSize: 10 }} interval={0} angle={-20} textAnchor="end" height={60} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#dc2626" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-slate-200">
        <div className="px-4 py-3 border-b border-slate-100 flex justify-between items-center">
          <h2 className="text-sm font-semibold text-slate-700">Critical Risk Projects</h2>
          <Link to="/risk-monitor" className="text-xs text-blue-600 hover:underline">View all →</Link>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
              <tr>
                <th className="text-left px-4 py-2">Project</th>
                <th className="text-left px-4 py-2">State</th>
                <th className="text-left px-4 py-2">Stage</th>
                <th className="text-left px-4 py-2">Risk</th>
                <th className="text-left px-4 py-2">Est. Delay</th>
                <th className="text-left px-4 py-2">Bottleneck</th>
              </tr>
            </thead>
            <tbody>
              {critical.map((p: any) => (
                <tr key={p.project_id} className="border-t border-slate-100 hover:bg-slate-50">
                  <td className="px-4 py-2">
                    <Link to={`/projects/${p.project_id}`} className="text-blue-700 font-medium hover:underline">
                      {p.project_id}
                    </Link>
                    <div className="text-xs text-slate-500 truncate max-w-xs">{p.project_name}</div>
                  </td>
                  <td className="px-4 py-2">{p.state}</td>
                  <td className="px-4 py-2 text-xs">{p.current_stage}</td>
                  <td className="px-4 py-2">
                    <span className={`inline-block px-2 py-0.5 rounded border text-xs font-semibold ${riskBg(p.risk_category)}`}>
                      {p.risk_score} · {p.risk_category}
                    </span>
                  </td>
                  <td className="px-4 py-2">{p.estimated_delay_days != null ? `${Math.round(p.estimated_delay_days)}d` : '—'}</td>
                  <td className="px-4 py-2 text-xs">{p.bottleneck_stage || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
