import { useState } from "react";
import api from "../api/client";
import { runOptimization, type OptimizationResponse } from "../api/hooks";
import { EquityChart, DrawdownChart } from "../components/Charts";
import { ErrorMessage } from "../components/ErrorMessage";
import "./shared.css";

const METRIC_TOOLTIPS: Record<string, string> = {
  total_return: "Overall portfolio return over the entire backtest period",
  cagr: "Compound Annual Growth Rate \u2014 annualized return",
  sharpe_ratio: "Risk-adjusted return. Higher = better return per unit of risk",
  max_drawdown: "Largest peak-to-trough decline. Lower absolute value is better",
  volatility: "Annualized standard deviation of daily returns. Lower = more stable",
  win_rate: "Fraction of trades that were profitable",
};

const AVAILABLE_PARAMS: Record<string, { label: string; defaults: number[] }> = {
  max_holdings: { label: "Max Holdings", defaults: [3, 5, 7] },
  max_concentration: { label: "Max Concentration", defaults: [0.2, 0.3, 0.4] },
  min_positions: { label: "Min Positions", defaults: [2, 3, 4] },
  max_turnover: { label: "Max Turnover", defaults: [0.3, 0.5, 0.7] },
};

const OPTIMIZABLE_METRICS = ["sharpe_ratio", "cagr", "total_return", "max_drawdown", "volatility"];

function formatMetricValue(key: string, v: number): string {
  const pctKeys = ["total_return", "cagr", "max_drawdown", "volatility", "win_rate"];
  if (pctKeys.includes(key)) return (v * 100).toFixed(2) + "%";
  if (key === "sharpe_ratio") return v.toFixed(2);
  return v.toFixed(4);
}

function BacktestSkeleton() {
  return (
    <div style={{ marginTop: "var(--space-4)" }}>
      <div className="metric-grid">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="skeleton-card">
            <div className="skeleton" style={{ width: "50%", height: 12 }} />
            <div className="skeleton" style={{ width: "70%", height: 28 }} />
          </div>
        ))}
      </div>
      <div className="skeleton" style={{ height: 300, borderRadius: "var(--radius-lg)", marginTop: "var(--space-4)" }} />
    </div>
  );
}

function ParamGridEditor({ grid, onChange }: { grid: Record<string, number[]>; onChange: (g: Record<string, number[]>) => void }) {
  const toggleParam = (key: string) => {
    if (grid[key]) {
      const next = { ...grid };
      delete next[key];
      onChange(next);
    } else {
      onChange({ ...grid, [key]: [...(AVAILABLE_PARAMS[key]?.defaults || [0.1, 0.2, 0.3])] });
    }
  };

  const updateValues = (key: string, raw: string) => {
    const nums = raw.split(",").map(s => parseFloat(s.trim())).filter(n => !isNaN(n));
    onChange({ ...grid, [key]: nums });
  };

  return (
    <div className="param-grid-editor">
      {Object.entries(AVAILABLE_PARAMS).map(([key, meta]) => {
        const active = !!grid[key];
        return (
          <div key={key} className={`param-row ${active ? "active" : ""}`}>
            <label className="param-toggle">
              <input type="checkbox" checked={active} onChange={() => toggleParam(key)} />
              <span>{meta.label}</span>
            </label>
            {active && (
              <input
                className="form-input param-values"
                type="text"
                value={grid[key].join(", ")}
                onChange={e => updateValues(key, e.target.value)}
                placeholder="comma-separated values"
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

function HeatmapCell({ value, metric, min, max }: { value: number; metric: string; min: number; max: number }) {
  const lowerIsBetter = metric === "max_drawdown" || metric === "volatility";
  let ratio: number;
  if (max === min) {
    ratio = 0.5;
  } else if (lowerIsBetter) {
    ratio = (value - max) / (min - max);
  } else {
    ratio = (value - min) / (max - min);
  }
  ratio = Math.max(0, Math.min(1, ratio));
  const r = Math.round(255 * (1 - ratio));
  const g = Math.round(200 * ratio);
  return (
    <span className="heatmap-cell" style={{ background: `rgba(${r}, ${g}, 60, 0.25)` }}>
      {formatMetricValue(metric, value)}
    </span>
  );
}

function SingleBacktest() {
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

  const computeDrawdown = (equity: { date: string; value: number }[]) => {
    let peak = equity[0]?.value || 0;
    return equity.map(p => {
      peak = Math.max(peak, p.value);
      return { date: p.date, drawdown: ((p.value - peak) / peak) * 100 };
    });
  };

  return (
    <>
      <div className="card" style={{ marginBottom: "var(--space-4)" }}>
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
        <button className="btn-primary" onClick={handleRun} disabled={loading || !isValid} style={{ marginTop: "var(--space-3)" }}>
          {loading ? "Running..." : "Run Backtest"}
        </button>
      </div>

      {error && <ErrorMessage message={error} onRetry={handleRun} />}
      {loading && <BacktestSkeleton />}

      {!runId && !loading && !error && (
        <div className="state-banner state-empty">
          <div className="state-empty-icon">{"\uD83D\uDCC9"}</div>
          <div className="state-empty-title">Configure and run a backtest</div>
          <div className="state-empty-desc">
            Set your date range and initial capital above, then run the backtest to see performance results.
          </div>
        </div>
      )}

      {results && (
        <div className="card">
          <div className="card-title">Results (Run #{runId})</div>
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
              <div className="card" style={{ marginTop: "var(--space-4)" }}>
                <div className="card-title">Equity Curve</div>
                <EquityChart data={results.equity_curve} />
              </div>
              <div className="card" style={{ marginTop: "var(--space-4)" }}>
                <div className="card-title">Drawdown</div>
                <DrawdownChart data={computeDrawdown(results.equity_curve)} />
              </div>
              <p style={{ color: "var(--color-text-dim)", marginTop: "var(--space-2)", fontSize: "var(--text-xs)" }}>
                {results.equity_curve.length} weekly snapshots, {results.trades?.length || 0} trades
              </p>
            </>
          )}
        </div>
      )}

      {results && (
        <button
          className="btn-secondary"
          onClick={() => window.open(`/api/reports/backtest/${runId}/pdf`, "_blank")}
          style={{ marginTop: "var(--space-4)" }}
        >
          Export Report
        </button>
      )}
    </>
  );
}

function OptimizationPanel() {
  const [form, setForm] = useState({ start_date: "2025-01-01", end_date: "2025-10-28", initial_capital: "100000" });
  const [paramGrid, setParamGrid] = useState<Record<string, number[]>>({
    max_holdings: [3, 5, 7],
    max_concentration: [0.2, 0.3, 0.4],
  });
  const [metric, setMetric] = useState("sharpe_ratio");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<OptimizationResponse | null>(null);

  const activeParamCount = Object.keys(paramGrid).length;
  const totalCombinations = activeParamCount > 0
    ? Object.values(paramGrid).reduce((acc, vals) => acc * Math.max(vals.length, 1), 1)
    : 0;

  const isValid = form.start_date && form.end_date && parseFloat(form.initial_capital) > 0
    && form.start_date < form.end_date && activeParamCount > 0 && totalCombinations <= 500;

  const handleRun = async () => {
    if (!isValid) return;
    setLoading(true); setError(null);
    try {
      const data = await runOptimization({
        start_date: form.start_date,
        end_date: form.end_date,
        initial_capital: parseFloat(form.initial_capital),
        param_grid: paramGrid,
        metric,
      });
      setResults(data);
    } catch (e: any) {
      const msg = e?.response?.data?.detail || e?.response?.data?.error || e.message || "Unknown error";
      setError(msg);
    }
    finally { setLoading(false); }
  };

  return (
    <>
      <div className="card" style={{ marginBottom: "var(--space-4)" }}>
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

        <div style={{ marginTop: "var(--space-4)" }}>
          <div className="card-title">Parameter Grid</div>
          <ParamGridEditor grid={paramGrid} onChange={setParamGrid} />
          <div className="param-grid-summary">
            {activeParamCount} parameters selected &rarr; {totalCombinations} combinations
            {totalCombinations > 500 && <span className="param-grid-warning"> (max 500)</span>}
          </div>
        </div>

        <div style={{ marginTop: "var(--space-4)" }}>
          <div className="card-title">Optimize For</div>
          <div className="metric-selector">
            {OPTIMIZABLE_METRICS.map(m => (
              <button
                key={m}
                className={`metric-btn ${metric === m ? "active" : ""}`}
                onClick={() => setMetric(m)}
              >
                {m.replace(/_/g, " ")}
              </button>
            ))}
          </div>
        </div>

        <button className="btn-primary" onClick={handleRun} disabled={loading || !isValid} style={{ marginTop: "var(--space-3)" }}>
          {loading ? "Optimizing..." : "Run Optimization"}
        </button>
      </div>

      {error && <ErrorMessage message={error} onRetry={handleRun} />}

      {loading && (
        <div className="card" style={{ marginTop: "var(--space-4)" }}>
          <div className="state-banner state-loading">
            <span className="state-loading-icon" />
            Running {totalCombinations} backtests in parallel...
          </div>
        </div>
      )}

      {!results && !loading && !error && (
        <div className="state-banner state-empty">
          <div className="state-empty-icon">{"\uD83D\uDD0D"}</div>
          <div className="state-empty-title">Grid search optimization</div>
          <div className="state-empty-desc">
            Select parameters and values to sweep, choose an optimization metric, then run to find the best combination.
          </div>
        </div>
      )}

      {results && <OptimizationPanel_Results data={results} />}
    </>
  );
}

function OptimizationPanel_Results({ data }: { data: OptimizationResponse }) {
  const metric = data.optimization_metric;
  const allVals = data.all_results.map(r => r.metrics[metric] ?? 0);
  const minVal = Math.min(...allVals);
  const maxVal = Math.max(...allVals);
  const paramKeys = data.all_results.length > 0 ? Object.keys(data.all_results[0].params) : [];

  return (
    <div className="card" style={{ marginTop: "var(--space-4)" }}>
      <div className="card-title">Optimization Results</div>
      <div className="metric-grid" style={{ marginBottom: "var(--space-4)" }}>
        <div className="metric-card">
          <div className="metric-label">Combinations</div>
          <div className="metric-value">{data.total_combinations}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Successful</div>
          <div className="metric-value positive">{data.successful_runs}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Failed</div>
          <div className="metric-value negative">{data.failed_runs}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Best {metric.replace(/_/g, " ")}</div>
          <div className="metric-value primary">{formatMetricValue(metric, data.best_metrics[metric] ?? 0)}</div>
        </div>
      </div>

      <div className="card-title" style={{ marginTop: "var(--space-4)" }}>Best Parameters</div>
      <div className="best-params">
        {Object.entries(data.best_params).map(([k, v]) => (
          <span key={k} className="best-param-badge">
            {k}: {typeof v === "number" && v < 1 && v > 0 ? (v * 100).toFixed(0) + "%" : v}
          </span>
        ))}
      </div>

      <div className="card-title" style={{ marginTop: "var(--space-4)" }}>All Combinations (ranked)</div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>#</th>
              {paramKeys.map(k => <th key={k}>{k}</th>)}
              <th>{metric.replace(/_/g, " ")}</th>
              <th>sharpe</th>
              <th>cagr</th>
              <th>max dd</th>
              <th>run</th>
            </tr>
          </thead>
          <tbody>
            {data.all_results.map((r, i) => (
              <tr key={i} className={i === 0 ? "best-row" : ""}>
                <td>{i + 1}</td>
                {paramKeys.map(k => (
                  <td key={k}>
                    {typeof r.params[k] === "number" && r.params[k] < 1 && r.params[k] > 0
                      ? (r.params[k] * 100).toFixed(0) + "%"
                      : r.params[k]}
                  </td>
                ))}
                <td>
                  <HeatmapCell value={r.metrics[metric] ?? 0} metric={metric} min={minVal} max={maxVal} />
                </td>
                <td>{formatMetricValue("sharpe_ratio", r.metrics.sharpe_ratio ?? 0)}</td>
                <td>{formatMetricValue("cagr", r.metrics.cagr ?? 0)}</td>
                <td>{formatMetricValue("max_drawdown", r.metrics.max_drawdown ?? 0)}</td>
                <td>
                  {r.run_id ? (
                    <a href="#" onClick={e => { e.preventDefault(); window.open(`/backtest?run=${r.run_id}`, "_self"); }}>
                      #{r.run_id}
                    </a>
                  ) : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Backtest() {
  const [tab, setTab] = useState<"single" | "optimize">("single");

  return (
    <div className="page">
      <h2>Backtest</h2>
      <div className="tab-bar">
        <button className={`tab-btn ${tab === "single" ? "active" : ""}`} onClick={() => setTab("single")}>
          Single Run
        </button>
        <button className={`tab-btn ${tab === "optimize" ? "active" : ""}`} onClick={() => setTab("optimize")}>
          Parameter Optimization
        </button>
      </div>
      {tab === "single" ? <SingleBacktest /> : <OptimizationPanel />}
    </div>
  );
}

export default Backtest;
