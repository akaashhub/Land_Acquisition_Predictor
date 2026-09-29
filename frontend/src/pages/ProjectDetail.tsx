import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api, riskBg } from '../services/api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>();
  const [p, setP] = useState<any>(null);
  const [updating, setUpdating] = useState(false);
  const [msg, setMsg] = useState('');
  const [form, setForm] = useState<any>({});

  const load = () => api.project(id!).then(setP).catch(e => setMsg(e.message));
  useEffect(() => { load(); }, [id]);

  if (!p) return <div className="text-slate-500">Loading project…</div>;

  const stageData = p.stage_risks
    ? Object.entries(p.stage_risks).map(([k, v]) => ({ stage: k, risk: v as number }))
    : [];

  const applyUpdate = async () => {
    setUpdating(true);
    try {
      const res = await api.updateProject(id!, form);
      setMsg(res.message || `Risk: ${res.prediction?.risk_score}`);
      setForm({});
      load();
    } catch (e: any) {
      setMsg(e.message);
    } finally {
      setUpdating(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <Link to="/projects" className="text-xs text-blue-600 hover:underline">← Projects</Link>
          <h1 className="text-xl font-semibold text-slate-800 mt-1">{p.project_id} · {p.project_name}</h1>
          <p className="text-sm text-slate-500">{p.project_type} · {p.district}, {p.state}</p>
        </div>
        <div className={`text-center px-6 py-3 rounded-lg border-2 ${riskBg(p.risk_category)}`}>
          <div className="text-3xl font-bold">{p.risk_score ?? '—'}</div>
          <div className="text-xs font-semibold tracking-wide">{p.risk_category || 'N/A'} / 100</div>
        </div>
      </div>

      {msg && <div className="bg-blue-50 border border-blue-200 text-blue-800 text-sm px-4 py-2 rounded">{msg}</div>}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          ['Delay Probability', `${p.delay_probability ?? p.probability ?? '—'}%`],
          ['Est. Delay', `${p.estimated_delay_days != null ? Math.round(p.estimated_delay_days) : '—'} days`],
          ['Current Stage', p.current_stage],
          ['Highest Risk Stage', p.bottleneck_stage || '—'],
        ].map(([l, v]) => (
          <div key={l as string} className="bg-white border border-slate-200 rounded-lg p-3 shadow-sm">
            <div className="text-xs text-slate-500">{l}</div>
            <div className="font-semibold text-slate-800 mt-0.5 text-sm">{v}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
          <h2 className="text-sm font-semibold text-slate-700 mb-2">WHY? — Top Risk Factors</h2>
          <ul className="space-y-2">
            {(p.top_risk_factors || []).slice(0, 6).map((f: any, i: number) => (
              <li key={i} className="flex items-start gap-2 text-sm">
                <span className="text-red-600 font-mono text-xs mt-0.5">+{f.contribution}</span>
                <div>
                  <div className="font-medium text-slate-700">{f.label}</div>
                  <div className="text-xs text-slate-500">{f.text}</div>
                </div>
              </li>
            ))}
            {!(p.top_risk_factors?.length) && <li className="text-sm text-slate-400">No significant risk factors</li>}
          </ul>
          {(p.protective_factors || []).length > 0 && (
            <>
              <h3 className="text-sm font-semibold text-green-700 mt-4 mb-2">Protective Factors</h3>
              <ul className="space-y-1">
                {p.protective_factors.slice(0, 4).map((f: any, i: number) => (
                  <li key={i} className="text-sm text-slate-600">✓ {f.text || f.label}</li>
                ))}
              </ul>
            </>
          )}
        </div>

        <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
          <h2 className="text-sm font-semibold text-slate-700 mb-2">WHAT SHOULD WE DO?</h2>
          <ol className="space-y-3">
            {(p.recommendations || []).map((r: any, i: number) => (
              <li key={i} className="text-sm border-l-2 border-blue-400 pl-3">
                <span className="text-xs font-semibold text-blue-700 uppercase">{r.category}</span>
                <p className="text-slate-700 mt-0.5">{r.recommendation}</p>
              </li>
            ))}
          </ol>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
        <h2 className="text-sm font-semibold text-slate-700 mb-3">Stage-wise Risk</h2>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={stageData} layout="vertical" margin={{ left: 100 }}>
            <XAxis type="number" domain={[0, 100]} />
            <YAxis type="category" dataKey="stage" width={100} tick={{ fontSize: 11 }} />
            <Tooltip />
            <Bar dataKey="risk" radius={[0, 4, 4, 0]}>
              {stageData.map((e, i) => (
                <Cell key={i} fill={e.risk > 70 ? '#dc2626' : e.risk > 50 ? '#ea580c' : e.risk > 30 ? '#ca8a04' : '#16a34a'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
        <h2 className="text-sm font-semibold text-slate-700 mb-3">Update Project (triggers re-prediction)</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            ['compensation_completion_percentage', 'Compensation %'],
            ['documentation_completion_percentage', 'Documentation %'],
            ['pending_approvals', 'Pending Approvals'],
            ['number_of_active_cases', 'Active Legal Cases'],
            ['stakeholder_response_rate', 'Stakeholder Response %'],
            ['unresolved_grievances', 'Unresolved Grievances'],
            ['dispute_severity', 'Dispute Severity (0-5)'],
          ].map(([k, label]) => (
            <label key={k} className="text-xs text-slate-600">
              {label}
              <input
                type="number"
                className="mt-1 w-full border border-slate-300 rounded px-2 py-1.5 text-sm"
                placeholder={String(p[k] ?? '')}
                value={form[k] ?? ''}
                onChange={e => setForm({ ...form, [k]: e.target.value === '' ? undefined : Number(e.target.value) })}
              />
            </label>
          ))}
          <label className="text-xs text-slate-600 flex items-center gap-2 mt-5">
            <input type="checkbox" checked={!!form.court_stay} onChange={e => setForm({ ...form, court_stay: e.target.checked })} />
            Court Stay Active
          </label>
          <label className="text-xs text-slate-600 flex items-center gap-2 mt-5">
            <input type="checkbox" checked={!!form.legal_dispute} onChange={e => setForm({ ...form, legal_dispute: e.target.checked })} />
            Legal Dispute
          </label>
        </div>
        <button
          onClick={applyUpdate}
          disabled={updating || Object.keys(form).length === 0}
          className="mt-4 bg-slate-800 text-white text-sm px-4 py-2 rounded hover:bg-slate-700 disabled:opacity-50"
        >
          {updating ? 'Updating…' : 'Save & Re-predict'}
        </button>
        <Link to={`/what-if?project=${id}`} className="ml-3 text-sm text-blue-600 hover:underline">Open What-If Simulator →</Link>
      </div>

      <div className="text-xs text-slate-400 border-t pt-3">
        Data completeness: {p.data_completeness}% · Predictions are model-based estimates from the demonstration dataset.
      </div>
    </div>
  );
}
