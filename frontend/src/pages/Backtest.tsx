import { useState } from "react";
import api from "../api/client";
import { EquityChart, DrawdownChart } from "../components/Charts";
import { ErrorMessage } from "../components/ErrorMessage";
import "./shared.css";

const METRIC_TOOLTIPS: Record<string, string> = {
  total_return: "Overall portfolio return over the entire backtest period",
  cagr: "Compound Annual Growth Rate — annualized return",
  sharpe_ratio: "Risk-adjusted return. Higher = better return per unit of risk",
  max_drawdown: "Largest peak-to-trough decline. Lower absolute value is better",
  volatility: "Annualized standard deviation of daily returns. Lower = more stable",
  win_rate: "Fraction of trades that were profitable",
};

function formatMetricValue(key: string, v: number): string {
  const pctKeys = ["total_return", "cagr", "max_drawdown", "volatility", "win_rate"];
  if (pctKeys.includes(key)) return (v * 100).toFixed(2) + "%";
  if (key === "sharpe_ratio") return v.toFixed(2);
  return v.toFixed(4);
}

function Backtest() {
  const [runId, setRunId] = useState<number | null>(null);
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({ start_date: "2025-01-01", end_date: "2025-10-28", initial_capital: "100000" });

  const isValid = form.start_date && form.end_date && parseFloat(form.initial_capital) > 0
    && form.start_date < form.end_date;

  const handleRun = async () => {
    if (!isValid) return;
    setLoading(true); setError(null);
    try {
      const { data } = await api.post("/backtest/run", {
        start_date: form.start_date.replace(/-/g, ""),
        end_date: form.end_date.replace(/-/g, ""),
        initial_capital: parseFloat(form.initial_capital),
      });
      const res = await api.get(`/backtest/results/${data.run_id}`);
      setRunId(data.run_id);
      setResults(res.data);
    } catch (e: any) {
      const msg = e?.response?.data?.detail || e.message || "Unknown error";
      setError(msg);
    }
    finally { setLoading(false); }
  };

  const computeDrawdown = (equity: { date: string; total_value: number }[]) => {
    let peak = equity[0]?.total_value || 0;
    return equity.map(p => {
      peak = Math.max(peak, p.total_value);
      return { date: p.date, drawdown: ((p.total_value - peak) / peak) * 100 };
    });
  };

  return (
    <div className="page">
      <h2>Backtest</h2>
      <div className="card" style={{marginBottom: 16}}>
        <div className="grid-col-3">
          <div className="form-group">
            <label>Start Date</label>
            <input className="form-input" type="date" value={form.start_date} onChange={e => setForm({...form, start_date: e.target.value})} />
          </div>
          <div className="form-group">
            <label>End Date</label>
            <input className="form-input" type="date" value={form.end_date} onChange={e => setForm({...form, end_date: e.target.value})} />
          </div>
          <div className="form-group">
            <label>Initial Capital</label>
            <input className="form-input" type="number" value={form.initial_capital} onChange={e => setForm({...form, initial_capital: e.target.value})} />
          </div>
        </div>
        <button className="btn-primary" onClick={handleRun} disabled={loading || !isValid} style={{marginTop:12}}>
          {loading ? "Running..." : "Run Backtest"}
        </button>
      </div>

      {error && <ErrorMessage message={error} onRetry={handleRun} />}

      {!runId && !loading && !error && (
        <div className="state-banner state-empty">Configure and run a backtest to see results.</div>
      )}

      {results && (
        <div className="card">
          <h3>Results (Run #{runId})</h3>
          <div className="metric-grid">
            {Object.entries(results.metrics || {}).map(([k, v]) => (
              <div key={k} className="metric-card">
                <div className="metric-label">
                  {k.replace(/_/g, " ")}
                  <span className="metric-help" title={METRIC_TOOLTIPS[k] || ""}>?</span>
                </div>
                <div className={"metric-value" + (k === "total_return" ? " primary" : "") + (typeof v === "number" && v > 0 ? " positive" : typeof v === "number" && v < 0 ? " negative" : "")}>
                  {typeof v === "number" ? formatMetricValue(k, v) : String(v)}
                </div>
              </div>
            ))}
          </div>
          {results.equity_curve && results.equity_curve.length > 0 && (
            <>
              <div className="card" style={{ marginTop: 16 }}>
                <h3>Equity Curve</h3>
                <EquityChart data={results.equity_curve} />
              </div>
              <div className="card" style={{ marginTop: 16 }}>
                <h3>Drawdown</h3>
                <DrawdownChart data={computeDrawdown(results.equity_curve)} />
              </div>
              <p style={{ color: 'var(--color-text-muted)', marginTop: 8 }}>
                {results.equity_curve.length} weekly snapshots, {results.trades?.length || 0} trades
              </p>
            </>
          )}
        </div>
      )}
    </div>
  );
}
export default Backtest;
