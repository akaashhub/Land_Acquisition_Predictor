import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, FolderKanban, AlertTriangle, Map, BarChart3,
  FlaskConical, Upload, Brain, Settings, LogOut, ShieldAlert
} from 'lucide-react';

const nav = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/projects', label: 'Projects', icon: FolderKanban },
  { to: '/risk-monitor', label: 'Risk Monitor', icon: ShieldAlert },
  { to: '/alerts', label: 'Early Warnings', icon: AlertTriangle },
  { to: '/map', label: 'Map', icon: Map },
  { to: '/analytics', label: 'Analytics', icon: BarChart3 },
  { to: '/what-if', label: 'What-If Simulator', icon: FlaskConical },
  { to: '/upload', label: 'Data Upload', icon: Upload },
  { to: '/model', label: 'Model Insights', icon: Brain },
  { to: '/settings', label: 'Settings', icon: Settings },
];

export default function Layout() {
  const navigate = useNavigate();
  const user = localStorage.getItem('username') || 'admin';
  const role = localStorage.getItem('role') || 'ADMIN';

  const logout = () => {
    localStorage.clear();
    navigate('/login');
  };

  return (
    <div className="flex min-h-screen bg-slate-100">
      <aside className="w-60 bg-slate-900 text-slate-200 flex flex-col shrink-0">
        <div className="px-4 py-5 border-b border-slate-700">
          <div className="text-xs uppercase tracking-widest text-slate-400">SIH 26017</div>
          <div className="font-semibold text-white text-sm leading-tight mt-1">
            Land Acquisition Delay Prediction
          </div>
          <div className="text-[10px] text-amber-400/90 mt-1">Demonstration · Synthetic Data</div>
        </div>
        <nav className="flex-1 py-3 overflow-y-auto">
          {nav.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-2.5 px-4 py-2.5 text-sm transition-colors ${
                  isActive ? 'bg-slate-800 text-white border-l-2 border-blue-400' : 'hover:bg-slate-800/60 text-slate-300'
                }`
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="p-4 border-t border-slate-700 text-xs">
          <div className="text-slate-400">{user} · {role}</div>
          <button onClick={logout} className="flex items-center gap-1.5 mt-2 text-slate-400 hover:text-white">
            <LogOut size={14} /> Sign out
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-auto">
        <header className="bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between sticky top-0 z-10">
          <div className="text-sm text-slate-500">
            PREDICT → EXPLAIN → RECOMMEND → SIMULATE → MONITOR
          </div>
          <div className="text-xs text-slate-400">
            Predictions support, not replace, administrative judgment
          </div>
        </header>
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
