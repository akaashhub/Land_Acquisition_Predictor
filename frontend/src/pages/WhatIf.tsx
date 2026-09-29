import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api, riskBg } from '../services/api';

export default function WhatIf() {
  const [params] = useSearchParams();
  const [projectId, setProjectId] = useState(params.get('project') || 'LA-1024');
  const [projects, setProjects] = useState<any[]>([]);
  const [changes, setChanges] = useState<any>({});
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.projects({ limit: 100, sort_by: 'risk_score' }).then(r => setProjects(r.items));
  }, []);

  const run = async () => {
    setLoading(true);
    try {
      const r = await api.whatIf(projectId, changes);
      setResult(r);
    } catch (e: any) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  };

  const fields = [
    { k: 'compensation_completion_percentage', label: 'Compensation %', type: 'number' },
    { k: 'documentation_completion_percentage', label: 'Documentation %', type: 'number' },
    { k: 'pending_approvals', label: 'Pending Approvals', type: 'number' },
    { k: 'number_of_active_cases', label: 'Active Legal Cases', type: 'number' },
    { k: 'stakeholder_response_rate', label: 'Stakeholder Response %', type: 'number' },
    { k: 'unresolved_grievances', label: 'Unresolved Grievances', type: 'number' },
    { k: 'dispute_severity', label: 'Dispute Severity', type: 'number' },
  ];

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-semibold text-slate-800">What-If Simulator</h1>
        <p className="text-sm text-slate-500">Simulate interventions without changing the live project record.</p>
      </div>

      <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm space-y-4">
        <label className="block text-sm">
          Project
          <select className="mt-1 w-full border border-slate-300 rounded px-3 py-2 text-sm"
            value={projectId} onChange={e => { setProjectId(e.target.value); setResult(null); }}>
            {projects.map(p => (
              <option key={p.project_id} value={p.project_id}>
                {p.project_id} — {p.risk_category} ({p.risk_score}) — {p.project_name?.slice(0, 40)}
              </option>
            ))}
          </select>
        </label>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {fields.map(f => (
            <label key={f.k} className="text-xs text-slate-600">
              {f.label}
              <input type="number" className="mt-1 w-full border border-slate-300 rounded px-2 py-1.5 text-sm"
                value={changes[f.k] ?? ''}
                onChange={e => setChanges({ ...changes, [f.k]: e.target.value === '' ? undefined : Number(e.target.value) })}
              />
            </label>
          ))}
          <label className="text-xs text-slate-600 flex items-center gap-2 mt-5">
            <input
  		type="checkbox"
  		checked={changes.court_stay === false}
  		onChange={e => setChanges({ ...changes, court_stay: e.target.checked ? false : true })}
	    />
            Resolve Court Stay
          </label>
          <label className="text-xs text-slate-600 flex items-center gap-2 mt-5">
            <input type="checkbox" checked={changes.legal_dispute === false}
              onChange={e => setChanges({ ...changes, legal_dispute: !e.target.checked })} />
            Clear Legal Dispute
          </label>
        </div>

        <button onClick={run} disabled={loading}
          className="bg-indigo-700 text-white text-sm px-5 py-2 rounded hover:bg-indigo-600 disabled:opacity-50">
          {loading ? 'Simulating…' : 'Run Simulation'}
        </button>
      </div>

      {result && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className={`rounded-lg border-2 p-4 ${riskBg(result.original.risk_category)}`}>
              <div className="text-xs uppercase">Current</div>
              <div className="text-3xl font-bold">{result.original.risk_score}</div>
              <div className="text-sm">{result.original.risk_category}</div>
              <div className="mt-2 h-3 bg-black/10 rounded overflow-hidden">
                <div className="h-full bg-current opacity-60" style={{ width: `${result.original.risk_score}%` }} />
              </div>
            </div>
            <div className={`rounded-lg border-2 p-4 ${riskBg(result.simulated.risk_category)}`}>
              <div className="text-xs uppercase">Simulated</div>
              <div className="text-3xl font-bold">{result.simulated.risk_score}</div>
              <div className="text-sm">{result.simulated.risk_category}</div>
              <div className="mt-2 h-3 bg-black/10 rounded overflow-hidden">
                <div className="h-full bg-current opacity-60" style={{ width: `${result.simulated.risk_score}%` }} />
              </div>
            </div>
          </div>
          <div className="bg-white border border-slate-200 rounded-lg p-4 text-sm">
            <strong>Risk change:</strong> {result.risk_change > 0 ? '↓' : '↑'} {Math.abs(result.risk_change)} points
            {result.risk_reduction > 0 && <span className="text-green-700 ml-2">(reduction of {result.risk_reduction})</span>}
            <div className="mt-2 text-xs text-slate-500">{result.disclaimer}</div>
          </div>
          <div className="bg-white border border-slate-200 rounded-lg p-4">
            <h3 className="text-sm font-semibold mb-2">Recommended after simulation</h3>
            <ul className="space-y-1 text-sm">
              {(result.recommendations || []).slice(0, 4).map((r: any, i: number) => (
                <li key={i} className="text-slate-700">• [{r.category}] {r.recommendation}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
