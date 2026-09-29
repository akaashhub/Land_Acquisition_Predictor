const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function getToken(): string | null {
  return localStorage.getItem('token');
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> || {}),
  };
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

export const api = {
  login: (username: string, password: string) =>
    request<{ access_token: string; role: string; username: string }>('/api/auth/login/json', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),
  overview: () => request<any>('/api/analytics/overview'),
  projects: (params: Record<string, string | number> = {}) => {
    const q = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => { if (v !== '' && v !== undefined) q.set(k, String(v)); });
    return request<{ total: number; items: any[] }>(`/api/projects?${q}`);
  },
  project: (id: string) => request<any>(`/api/projects/${id}`),
  predict: (id: string) => request<any>(`/api/projects/${id}/predict`, { method: 'POST' }),
  updateProject: (id: string, data: any) =>
    request<any>(`/api/projects/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  whatIf: (id: string, changes: any) =>
    request<any>(`/api/projects/${id}/what-if`, { method: 'POST', body: JSON.stringify({ changes }) }),
  alerts: (status?: string) =>
    request<{ items: any[]; unread_count: number }>(`/api/alerts${status ? `?status=${status}` : ''}`),
  markAlertRead: (id: number) => request(`/api/alerts/${id}/read`, { method: 'PUT' }),
  states: () => request<any>('/api/analytics/states'),
  districts: (state?: string) =>
    request<any>(`/api/analytics/districts${state ? `?state=${state}` : ''}`),
  riskDist: () => request<any>('/api/analytics/risk-distribution'),
  stageBottlenecks: () => request<any>('/api/analytics/stage-bottlenecks'),
  mapData: () => request<{ items: any[] }>('/api/analytics/map'),
  modelMetrics: () => request<any>('/api/model/metrics'),
  predictedVsActual: () => request<any>('/api/analytics/predicted-vs-actual'),
  uploadCsv: async (file: File) => {
    const fd = new FormData();
    fd.append('file', file);
    const token = getToken();
    const res = await fetch(`${API_URL}/api/upload/csv`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: fd,
    });
    if (!res.ok) throw new Error((await res.json()).detail || 'Upload failed');
    return res.json();
  },
};

export function riskColor(cat: string): string {
  switch ((cat || '').toUpperCase()) {
    case 'LOW': return '#16a34a';
    case 'MEDIUM': return '#ca8a04';
    case 'HIGH': return '#ea580c';
    case 'CRITICAL': return '#dc2626';
    default: return '#6b7280';
  }
}

export function riskBg(cat: string): string {
  switch ((cat || '').toUpperCase()) {
    case 'LOW': return 'bg-green-100 text-green-800 border-green-300';
    case 'MEDIUM': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    case 'HIGH': return 'bg-orange-100 text-orange-800 border-orange-300';
    case 'CRITICAL': return 'bg-red-100 text-red-800 border-red-300';
    default: return 'bg-gray-100 text-gray-700 border-gray-300';
  }
}
