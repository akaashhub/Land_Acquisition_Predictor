import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export default function ModelInsights() {
  const [m, setM] = useState<any>(null);
  useEffect(() => { api.modelMetrics().then(setM); }, []);
  if (!m) return <div className="text-slate-500">Loading…</div>;
  const cm = m.classifier_metrics || {};
  const fi = Object.entries(m.feature_importance || {}).map(([k, v]) => ({ feature: k, importance: v as number })).slice(0, 12);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-800">Model Insights</h1>
        <p className="text-sm text-amber-700 mt-1">{m.disclaimer}</p>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          ['Classifier', m.classifier],
          ['Training size', m.training_size],
          ['Features', m.n_features],
          ['Recall', cm.recall != null ? (cm.recall * 100).toFixed(1) + '%' : '—'],
          ['Precision', cm.precision != null ? (cm.precision * 100).toFixed(1) + '%' : '—'],
          ['F1', cm.f1 != null ? (cm.f1 * 100).toFixed(1) + '%' : '—'],
          ['ROC-AUC', cm.roc_auc != null ? cm.roc_auc.toFixed(3) : '—'],
          ['Accuracy', cm.accuracy != null ? (cm.accuracy * 100).toFixed(1) + '%' : '—'],
        ].map(([l, v]) => (
          <div key={l as string} className="bg-white border border-slate-200 rounded-lg p-3 shadow-sm">
            <div className="text-xs text-slate-500">{l}</div>
            <div className="font-semibold text-slate-800">{v}</div>
          </div>
        ))}
      </div>
      <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
        <h2 className="text-sm font-semibold mb-3">Top Feature Importance</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={fi} layout="vertical" margin={{ left: 140 }}>
            <XAxis type="number" />
            <YAxis type="category" dataKey="feature" width={140} tick={{ fontSize: 10 }} />
            <Tooltip />
            <Bar dataKey="importance" fill="#1e40af" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      {m.regressor_metrics && (
        <div className="text-sm text-slate-600">
          Delay regressor ({m.regressor}): MAE={m.regressor_metrics.mae?.toFixed(1)},
          RMSE={m.regressor_metrics.rmse?.toFixed(1)}, R²={m.regressor_metrics.r2?.toFixed(3)}
        </div>
      )}
    </div>
  );
}
