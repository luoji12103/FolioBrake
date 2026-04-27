import { useState } from "react";
import { useBacktestResults, useMutation, BacktestResult } from "../api/hooks";
import "./shared.css";

/* ---- Format helpers ---- */

function fmtCurrency(v: number): string {
  return new Intl.NumberFormat("zh-CN", {
    style: "currency",
    currency: "CNY",
    minimumFractionDigits: 0,
  }).format(v);
}

function fmtPct(v: number): string {
  return `${(v * 100).toFixed(2)}%`;
}

function fmtNum(v: number, d = 2): string {
  return v.toFixed(d);
}

function fmtDate(d: string): string {
  return new Date(d).toLocaleDateString("en-CN");
}

/* ---- Skeleton ---- */

function BacktestSkeleton() {
  return (
    <div style={{ marginTop: 16 }}>
      <div className="skeleton" style={{ height: 300, marginBottom: 20 }} />
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 16, marginBottom: 20 }}>
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="skeleton" style={{ height: 90 }} />
        ))}
      </div>
    </div>
  );
}

/* ---- Form ---- */

interface FormState {
  strategy: string;
  startDate: string;
  endDate: string;
  initialCapital: number;
  benchmark: string;
}

const defaultForm: FormState = {
  strategy: "momentum_rotation",
  startDate: "2024-01-01",
  endDate: "2025-01-01",
  initialCapital: 1000000,
  benchmark: "510300",
};

function BacktestForm({
  onSubmit,
  isLoading,
}: {
  onSubmit: (form: FormState) => void;
  isLoading: boolean;
}) {
  const [form, setForm] = useState<FormState>(defaultForm);

  const update = (key: keyof FormState, value: string | number) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(form);
  };

  return (
    <form onSubmit={handleSubmit} className="card">
      <div className="card-title">Backtest Configuration</div>
      <div className="grid-col-2">
        <div className="form-group">
          <label htmlFor="bt-strategy">Strategy</label>
          <select
            id="bt-strategy"
            className="form-input"
            value={form.strategy}
            onChange={(e) => update("strategy", e.target.value)}
          >
            <option value="momentum_rotation">Momentum Rotation</option>
            <option value="min_variance">Minimum Variance</option>
            <option value="equal_weight">Equal Weight</option>
            <option value="risk_parity">Risk Parity</option>
            <option value="trend_following">Trend Following</option>
          </select>
        </div>
        <div className="form-group">
          <label htmlFor="bt-benchmark">Benchmark</label>
          <select
            id="bt-benchmark"
            className="form-input"
            value={form.benchmark}
            onChange={(e) => update("benchmark", e.target.value)}
          >
            <option value="510300">CSI 300 (510300)</option>
            <option value="510050">SSE 50 (510050)</option>
            <option value="510500">CSI 500 (510500)</option>
            <option value="159919">CSI 300 ETF (159919)</option>
          </select>
        </div>
        <div className="form-group">
          <label htmlFor="bt-start">Start Date</label>
          <input
            id="bt-start"
            type="date"
            className="form-input"
            value={form.startDate}
            onChange={(e) => update("startDate", e.target.value)}
          />
        </div>
        <div className="form-group">
          <label htmlFor="bt-end">End Date</label>
          <input
            id="bt-end"
            type="date"
            className="form-input"
            value={form.endDate}
            onChange={(e) => update("endDate", e.target.value)}
          />
        </div>
        <div className="form-group">
          <label htmlFor="bt-capital">Initial Capital (CNY)</label>
          <input
            id="bt-capital"
            type="number"
            className="form-input"
            value={form.initialCapital}
            onChange={(e) =>
              update("initialCapital", Number(e.target.value))
            }
            min={10000}
            step={10000}
          />
        </div>
      </div>
      <div style={{ marginTop: 16 }}>
        <button type="submit" className="btn btn-primary" disabled={isLoading}>
          {isLoading ? (
            <>
              <span className="state-loading-icon" />
              Running...
            </>
          ) : (
            "Run Backtest"
          )}
        </button>
      </div>
    </form>
  );
}

/* ---- Metrics cards ---- */

function MetricsCards({ metrics }: { metrics: BacktestResult["metrics"] }) {
  return (
    <div className="metrics-grid">
      <div className="metric-card">
        <div className="metric-label">Total Return</div>
        <div
          className={`metric-value ${metrics.total_return >= 0 ? "positive" : "negative"}`}
        >
          {fmtPct(metrics.total_return)}
        </div>
      </div>
      <div className="metric-card">
        <div className="metric-label">Annual Return</div>
        <div
          className={`metric-value ${metrics.annual_return >= 0 ? "positive" : "negative"}`}
        >
          {fmtPct(metrics.annual_return)}
        </div>
      </div>
      <div className="metric-card">
        <div className="metric-label">Sharpe Ratio</div>
        <div
          className={`metric-value ${metrics.sharpe_ratio >= 0 ? "positive" : "negative"}`}
        >
          {fmtNum(metrics.sharpe_ratio)}
        </div>
      </div>
      <div className="metric-card">
        <div className="metric-label">Max Drawdown</div>
        <div className="metric-value negative">
          {fmtPct(metrics.max_drawdown)}
        </div>
      </div>
      <div className="metric-card">
        <div className="metric-label">Win Rate</div>
        <div
          className={`metric-value ${metrics.win_rate >= 0.5 ? "positive" : "negative"}`}
        >
          {fmtPct(metrics.win_rate)}
        </div>
      </div>
      <div className="metric-card">
        <div className="metric-label">Volatility</div>
        <div className="metric-value" style={{ color: "var(--color-text)" }}>
          {fmtPct(metrics.volatility)}
        </div>
      </div>
    </div>
  );
}

/* ---- Equity curve placeholder ---- */

function EquityCurvePlaceholder() {
  return (
    <div className="card">
      <div className="card-title">Equity Curve</div>
      <div
        style={{
          height: 300,
          background: "var(--color-bg)",
          borderRadius: 8,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "var(--color-text-muted)",
          fontSize: 14,
          border: "1px dashed var(--color-border)",
        }}
      >
        <div style={{ textAlign: "center" }}>
          <div
            style={{
              fontSize: 32,
              marginBottom: 8,
              opacity: 0.5,
            }}
          >
            📈
          </div>
          <div>Chart coming soon</div>
          <div
            style={{
              fontSize: 12,
              marginTop: 4,
              opacity: 0.7,
            }}
          >
            Equity curve visualization will render here
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---- Trade log ---- */

function TradeLog({ trades }: { trades: BacktestResult["trade_log"] }) {
  if (!trades || trades.length === 0) {
    return (
      <div className="card">
        <div className="card-title">Trade Log</div>
        <p style={{ color: "var(--color-text-muted)", fontSize: 14 }}>
          No trades recorded.
        </p>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-title">
        Trade Log ({trades.length} trades)
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Symbol</th>
              <th>Action</th>
              <th>Quantity</th>
              <th>Price</th>
              <th>Notional</th>
              <th>Reason</th>
            </tr>
          </thead>
          <tbody>
            {trades.map((t, i) => (
              <tr key={`${t.date}-${t.symbol}-${i}`}>
                <td>{fmtDate(t.date)}</td>
                <td style={{ fontWeight: 600 }}>{t.symbol}</td>
                <td>
                  <span
                    className={`badge ${t.action === "BUY" ? "badge-buy" : "badge-sell"}`}
                  >
                    {t.action}
                  </span>
                </td>
                <td>{t.quantity.toLocaleString()}</td>
                <td>{fmtNum(t.price)}</td>
                <td>{fmtCurrency(t.notional)}</td>
                <td style={{ whiteSpace: "normal", maxWidth: 200, fontSize: 13 }}>
                  {t.reason}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ---- Benchmark comparison ---- */

function BenchmarkComparison({
  rows,
}: {
  rows: BacktestResult["benchmark_comparison"];
}) {
  if (!rows || rows.length === 0) return null;

  return (
    <div className="card">
      <div className="card-title">Benchmark Comparison</div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Metric</th>
              <th>Strategy</th>
              <th>Benchmark</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i}>
                <td>{r.metric}</td>
                <td style={{ fontWeight: 600 }}>
                  {typeof r.strategy === "number"
                    ? r.strategy >= 0
                      ? fmtPct(r.strategy)
                      : fmtPct(r.strategy)
                    : r.strategy}
                </td>
                <td>
                  {typeof r.benchmark === "number"
                    ? r.benchmark >= 0
                      ? fmtPct(r.benchmark)
                      : fmtPct(r.benchmark)
                    : r.benchmark}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ---- Results section ---- */

function BacktestResults({ result }: { result: BacktestResult }) {
  return (
    <div style={{ marginTop: 24 }}>
      <h3 className="section-title">
        Results: {result.config.strategy.replace(/_/g, " ")} |{" "}
        {result.config.start_date} to {result.config.end_date} |{" "}
        Initial Capital: {fmtCurrency(result.config.initial_capital)}
      </h3>

      <MetricsCards metrics={result.metrics} />
      <EquityCurvePlaceholder />
      <TradeLog trades={result.trade_log} />
      <BenchmarkComparison rows={result.benchmark_comparison} />
    </div>
  );
}

/* ---- Page ---- */

function Backtest() {
  const [runId, setRunId] = useState<string | null>(null);
  const {
    data: result,
    error: fetchError,
    isLoading: isFetching,
  } = useBacktestResults(runId);
  const {
    error: runError,
    isLoading: isRunning,
    mutate: runBacktest,
  } = useMutation<{ run_id: string }>("post", "/backtest/run");

  const handleRun = async (form: FormState) => {
    const res = await runBacktest({
      strategy: form.strategy,
      start_date: form.startDate,
      end_date: form.endDate,
      initial_capital: form.initialCapital,
      benchmark: form.benchmark,
    });
    if (res && res.run_id) {
      setRunId(res.run_id);
    }
  };

  const displayError = runError || fetchError;
  const displayLoading = isRunning || isFetching;

  return (
    <div className="page">
      <h2>Backtest</h2>

      <BacktestForm onSubmit={handleRun} isLoading={isRunning} />

      {displayLoading && <BacktestSkeleton />}

      {displayError && (
        <div className="state-banner state-error">
          <span>Backtest failed: {displayError}</span>
        </div>
      )}

      {!displayLoading && !displayError && !result && !runId && (
        <div className="state-banner state-empty">
          Configure your backtest above and click Run to see results.
        </div>
      )}

      {!displayLoading && result && (
        <BacktestResults result={result} />
      )}
    </div>
  );
}

export default Backtest;
