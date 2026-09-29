import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';

export default function Alerts() {
  const [items, setItems] = useState<any[]>([]);
  const [unread, setUnread] = useState(0);

  const load = () => api.alerts().then(r => { setItems(r.items); setUnread(r.unread_count); });
  useEffect(() => { load(); }, []);

  const mark = async (id: number) => {
    await api.markAlertRead(id);
    load();
  };

  const sevColor: Record<string, string> = {
    CRITICAL: 'border-red-500 bg-red-50',
    HIGH: 'border-orange-500 bg-orange-50',
    WARNING: 'border-yellow-500 bg-yellow-50',
    INFO: 'border-blue-400 bg-blue-50',
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold text-slate-800">Early Warnings</h1>
        <span className="text-sm text-slate-500">{unread} unread</span>
      </div>
      <div className="space-y-3">
        {items.map(a => (
          <div key={a.id} className={`border-l-4 rounded-lg p-4 shadow-sm bg-white ${sevColor[a.severity] || 'border-slate-300'}`}>
            <div className="flex justify-between gap-2">
              <div>
                <span className="text-xs font-bold uppercase text-slate-600">{a.severity}</span>
                <span className="mx-2 text-slate-300">·</span>
                <Link to={`/projects/${a.project_id}`} className="text-blue-700 font-medium text-sm hover:underline">{a.project_id}</Link>
              </div>
              <div className="text-xs text-slate-400">{a.created_at ? new Date(a.created_at).toLocaleString() : ''}</div>
            </div>
            <p className="text-sm text-slate-800 mt-1">{a.message}</p>
            {a.recommended_action && (
              <p className="text-xs text-slate-600 mt-1"><strong>Action:</strong> {a.recommended_action}</p>
            )}
            {a.status === 'unread' && (
              <button onClick={() => mark(a.id)} className="mt-2 text-xs text-blue-600 hover:underline">Mark read</button>
            )}
          </div>
        ))}
        {items.length === 0 && <p className="text-slate-500 text-sm">No alerts yet.</p>}
      </div>
    </div>
  );
}
