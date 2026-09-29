import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';

export default function Login() {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin123');
  const [err, setErr] = useState('');
  const navigate = useNavigate();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const r = await api.login(username, password);
      localStorage.setItem('token', r.access_token);
      localStorage.setItem('role', r.role);
      localStorage.setItem('username', r.username);
      navigate('/');
    } catch (e: any) {
      setErr(e.message || 'Login failed');
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      <form onSubmit={submit} className="bg-white rounded-xl shadow-xl p-8 w-full max-w-md space-y-4">
        <div>
          <div className="text-xs uppercase tracking-widest text-slate-400">SIH 26017</div>
          <h1 className="text-xl font-semibold text-slate-800">Land Acquisition Delay Prediction</h1>
          <p className="text-xs text-amber-600 mt-1">Demonstration Dataset — Synthetic Data</p>
        </div>
        {err && <div className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded">{err}</div>}
        <label className="block text-sm">
          Username
          <input className="mt-1 w-full border border-slate-300 rounded px-3 py-2" value={username}
            onChange={e => setUsername(e.target.value)} />
        </label>
        <label className="block text-sm">
          Password
          <input type="password" className="mt-1 w-full border border-slate-300 rounded px-3 py-2" value={password}
            onChange={e => setPassword(e.target.value)} />
        </label>
        <button type="submit" className="w-full bg-slate-800 text-white py-2.5 rounded-lg hover:bg-slate-700">
          Sign in
        </button>
        <div className="text-xs text-slate-500 border-t pt-3">
          Demo credentials: admin / admin123 · officer / officer123 · viewer / viewer123
        </div>
      </form>
    </div>
  );
}
