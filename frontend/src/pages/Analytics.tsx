import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export default function Analytics() {
  const [states, setStates] = useState<any[]>([]);
  const [districts, setDistricts] = useState<any[]>([]);

  useEffect(() => {
    api.states().then(r => setStates(r.items || []));
    api.districts().then(r => setDistricts(r.items || []));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-800">State & District Analytics</h1>
        <p className="text-sm text-slate-500">Highest-risk areas in the demonstration dataset.</p>
      </div>
      <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
        <h2 className="text-sm font-semibold mb-3">Average Risk by State</h2>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={states}>
            <XAxis dataKey="state" tick={{ fontSize: 10 }} angle={-25} textAnchor="end" height={70} />
            <YAxis domain={[0, 100]} />
            <Tooltip />
            <Bar dataKey="average_risk" fill="#dc2626" radius={[4, 4, 0, 0]} name="Avg Risk" />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              <th className="text-left px-3 py-2">State</th>
              <th className="text-left px-3 py-2">Projects</th>
              <th className="text-left px-3 py-2">High</th>
              <th className="text-left px-3 py-2">Critical</th>
              <th className="text-left px-3 py-2">Avg Risk</th>
              <th className="text-left px-3 py-2">Avg Delay</th>
            </tr>
          </thead>
          <tbody>
            {states.map(s => (
              <tr key={s.state} className="border-t border-slate-100">
                <td className="px-3 py-2 font-medium">{s.state}</td>
                <td className="px-3 py-2">{s.projects}</td>
                <td className="px-3 py-2">{s.high_risk}</td>
                <td className="px-3 py-2 text-red-700 font-semibold">{s.critical}</td>
                <td className="px-3 py-2">{s.average_risk}</td>
                <td className="px-3 py-2">{s.average_delay}d</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-x-auto">
        <div className="px-4 py-3 border-b text-sm font-semibold">Top Districts by Risk</div>
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              <th className="text-left px-3 py-2">District</th>
              <th className="text-left px-3 py-2">State</th>
              <th className="text-left px-3 py-2">Projects</th>
              <th className="text-left px-3 py-2">Critical</th>
              <th className="text-left px-3 py-2">Avg Risk</th>
            </tr>
          </thead>
          <tbody>
            {districts.slice(0, 15).map(d => (
              <tr key={`${d.state}-${d.district}`} className="border-t border-slate-100">
                <td className="px-3 py-2 font-medium">{d.district}</td>
                <td className="px-3 py-2">{d.state}</td>
                <td className="px-3 py-2">{d.projects}</td>
                <td className="px-3 py-2 text-red-700">{d.critical}</td>
                <td className="px-3 py-2">{d.average_risk}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
