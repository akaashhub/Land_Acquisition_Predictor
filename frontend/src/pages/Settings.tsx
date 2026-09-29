export default function Settings() {
  return (
    <div className="space-y-4 max-w-xl">
      <h1 className="text-2xl font-semibold text-slate-800">Settings</h1>
      <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm text-sm space-y-2">
        <p><strong>System:</strong> SIH26017 Predictive Analytics Prototype</p>
        <p><strong>Dataset:</strong> Demonstration Dataset — Synthetic Data</p>
        <p><strong>Risk thresholds (prototype):</strong> 0–25 LOW · 26–50 MEDIUM · 51–75 HIGH · 76–100 CRITICAL</p>
        <p><strong>API:</strong> {import.meta.env.VITE_API_URL || 'http://localhost:8000'}</p>
        <p className="text-xs text-slate-500 mt-3">
          Predictions are estimates generated from the available demonstration dataset and model.
          They should support, not replace, administrative judgment. The synthetic dataset must be
          replaced or retrained using validated real-world government data before production deployment.
        </p>
      </div>
    </div>
  );
}
