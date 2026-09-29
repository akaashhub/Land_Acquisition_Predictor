import { useState } from 'react';
import { api } from '../services/api';

export default function Upload() {
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const onFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    try {
      const r = await api.uploadCsv(file);
      setResult(r);
    } catch (err: any) {
      setResult({ error: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4 max-w-2xl">
      <h1 className="text-2xl font-semibold text-slate-800">CSV Data Ingestion</h1>
      <p className="text-sm text-slate-500">
        Upload → Schema Validation → Feature Engineering → ML Prediction → Risk Classification
      </p>
      <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm">
        <input type="file" accept=".csv" onChange={onFile} className="text-sm" />
        <p className="text-xs text-slate-400 mt-2">Requires ADMIN role. Sample CSV available from API /api/upload/sample-csv/download</p>
        {loading && <p className="mt-3 text-sm text-slate-500">Processing…</p>}
        {result && (
          <div className="mt-4 text-sm space-y-1">
            {result.error ? (
              <p className="text-red-600">{result.error}</p>
            ) : (
              <>
                <p>Total rows: {result.total_rows}</p>
                <p>Valid: {result.valid_rows} · Invalid: {result.invalid_rows}</p>
                {result.confidence_note && <p className="text-amber-700">{result.confidence_note}</p>}
                <p className="text-xs text-slate-400">{result.disclaimer}</p>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
