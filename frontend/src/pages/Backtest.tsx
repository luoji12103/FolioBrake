import { useState } from "react";
import api from "../api/client";
import "./shared.css";

function Backtest() {
  const [runId, setRunId] = useState<number | null>(null);
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({ start_date: "2025-01-01", end_date: "2025-10-28", initial_capital: "100000" });

  const handleRun = async () => {
    setLoading(true); setError(null);
    try {
      const { data } = await api.post("/backtest/run", {
        start_date: form.start_date, end_date: form.end_date,
        initial_capital: parseFloat(form.initial_capital),
      });
      const res = await api.get(`/backtest/results/${data.run_id}`);
      setRunId(data.run_id);
      setResults(res.data);
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  return (
    <div className="page">
      <h2>Backtest</h2>
      <div className="card" style={{marginBottom: 16}}>
        <div className="grid-col-3">
          <div className="form-group">
            <label>Start Date</label>
            <input className="form-input" value={form.start_date} onChange={e => setForm({...form, start_date: e.target.value})} />
          </div>
          <div className="form-group">
            <label>End Date</label>
            <input className="form-input" value={form.end_date} onChange={e => setForm({...form, end_date: e.target.value})} />
          </div>
          <div className="form-group">
            <label>Initial Capital</label>
            <input className="form-input" type="number" value={form.initial_capital} onChange={e => setForm({...form, initial_capital: e.target.value})} />
          </div>
        </div>
        <button className="btn-primary" onClick={handleRun} disabled={loading} style={{marginTop:12}}>
          {loading ? "Running..." : "Run Backtest"}
        </button>
      </div>

      {error && <div className="state-banner state-error">Error: {error}</div>}

      {!runId && !loading && !error && (
        <div className="state-banner state-empty">Configure and run a backtest to see results.</div>
      )}

      {results && (
        <div className="card">
          <h3>Results (Run #{runId})</h3>
          <div className="metric-grid">
            {Object.entries(results.metrics || {}).map(([k,v]) => (
              <div key={k} className="metric-card">
                <div className="metric-value">{typeof v === 'number' ? (v * 100).toFixed(2) + '%' : String(v)}</div>
                <div className="metric-label">{k.replace(/_/g, ' ')}</div>
              </div>
            ))}
          </div>
          {results.equity_curve && results.equity_curve.length > 0 && (
            <p style={{color: 'var(--color-text-muted)', marginTop: 8}}>
              {results.equity_curve.length} weekly snapshots, {results.trades?.length || 0} trades
            </p>
          )}
        </div>
      )}
    </div>
  );
}
export default Backtest;
