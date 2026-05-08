import { useEffect, useState } from "react";
import { healthCheck } from "../api/client";
import { useRiskState, useSignals, usePortfolio, usePaperPortfolios, usePaperPerformance, useRealtimePrices } from "../api/hooks";
import { EquityChart, DrawdownChart } from "../components/Charts";
import { ErrorMessage } from "../components/ErrorMessage";
import "./shared.css";

function DashboardSkeleton() {
  return (
    <div style={{ marginTop: 4 }}>
      <div className="metric-grid">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="skeleton-card">
            <div className="skeleton" style={{ width: "40%", height: 12 }} />
            <div className="skeleton" style={{ width: "65%", height: 28 }} />
          </div>
        ))}
      </div>
    </div>
  );
}

function Dashboard() {
  const [health, setHealth] = useState<{ status: string; version: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [healthLoading, setHealthLoading] = useState(true);
  const { data: riskState } = useRiskState();
  const { data: signals } = useSignals();
  const { data: portfolio } = usePortfolio();
  const { data: portfolios } = usePaperPortfolios();
  const { data: performance } = usePaperPerformance(portfolios?.[0]?.id?.toString() || null);
  const { data: priceUpdate, connected: wsConnected } = useRealtimePrices();

  const fetchHealth = () => {
    setError(null);
    setHealthLoading(true);
    healthCheck()
      .then(setHealth)
      .catch((err) => setError(err.message))
      .finally(() => setHealthLoading(false));
  };

  useEffect(() => { fetchHealth(); }, []);

  const topSignal = signals && signals.length > 0
    ? [...signals].sort((a, b) => b.score - a.score)[0]
    : null;

  const riskColor: Record<string, string> = {
    NORMAL: "var(--color-green)",
    CAUTION: "var(--color-yellow)",
    DEFENSIVE: "var(--color-orange)",
    HALT: "var(--color-red)",
  };

  return (
    <div className="page">
      <h2>Dashboard</h2>

      {error && <ErrorMessage message={`Backend offline: ${error}`} onRetry={fetchHealth} />}

      {healthLoading && <DashboardSkeleton />}

      {health && (
        <div className="metric-grid">
          <div className="metric-card">
            <div className="metric-label">Risk State</div>
            <div
              className="metric-value"
              style={{ color: riskColor[riskState?.state || "NORMAL"] || "var(--color-text)" }}
            >
              {riskState?.state || "NORMAL"}
            </div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Portfolio</div>
            <div className="metric-value">
              {portfolio ? `${portfolio.length}` : "\u2014"}
              {portfolio && (
                <span style={{ fontSize: "var(--text-sm)", color: "var(--color-text-dim)", marginLeft: 4, fontWeight: 500 }}>
                  ETFs
                </span>
              )}
            </div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Top Signal</div>
            <div className="metric-value" style={{ fontSize: "var(--text-xl)" }}>
              {topSignal ? (
                <>
                  <span style={{ color: "var(--color-accent)" }}>{topSignal.symbol}</span>
                  <span style={{ fontSize: "var(--text-sm)", color: "var(--color-text-dim)", marginLeft: 6, fontWeight: 500 }}>
                    {topSignal.score.toFixed(1)}
                  </span>
                </>
              ) : "\u2014"}
            </div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Next Rebalance</div>
            <div className="metric-value" style={{ fontSize: "var(--text-xl)" }}>Friday</div>
          </div>
          <div className="metric-card">
            <div className="metric-label">
              Live Price
              <span
                style={{
                  display: "inline-block",
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  backgroundColor: wsConnected ? "var(--color-green)" : "var(--color-red)",
                  marginLeft: 6,
                  verticalAlign: "middle",
                }}
              />
            </div>
            <div className="metric-value" style={{ fontSize: "var(--text-xl)" }}>
              {priceUpdate ? (
                <>
                  <span style={{ color: "var(--color-accent)" }}>{priceUpdate.symbol}</span>
                  <span style={{ marginLeft: 6 }}>{priceUpdate.price.toFixed(3)}</span>
                  <span
                    style={{
                      fontSize: "var(--text-sm)",
                      marginLeft: 6,
                      color: priceUpdate.change >= 0 ? "var(--color-green)" : "var(--color-red)",
                    }}
                  >
                    {priceUpdate.change >= 0 ? "+" : ""}
                    {priceUpdate.change_pct.toFixed(2)}%
                  </span>
                </>
              ) : (
                <span style={{ color: "var(--color-text-dim)" }}>{"\u2014"}</span>
              )}
            </div>
          </div>
        </div>
      )}

      {performance && performance.equity_curve.length > 0 && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div className="card-title">Portfolio Performance</div>
          <EquityChart data={performance.equity_curve} benchmarkData={performance.benchmark_curve} />
          <div style={{ marginTop: 16 }}>
            <DrawdownChart data={performance.drawdown_curve} />
          </div>
          <div className="metric-grid" style={{ marginTop: 16 }}>
            <div className="metric-card">
              <div className="metric-label">CAGR</div>
              <div className="metric-value">{(performance.metrics.cagr * 100).toFixed(1)}%</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Sharpe</div>
              <div className="metric-value">{performance.metrics.sharpe_ratio.toFixed(2)}</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Max DD</div>
              <div className="metric-value">{(performance.metrics.max_drawdown * 100).toFixed(1)}%</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Win Rate</div>
              <div className="metric-value">{(performance.metrics.win_rate * 100).toFixed(0)}%</div>
            </div>
          </div>
        </div>
      )}

      {signals && signals.length > 0 && (
        <div className="card">
          <div className="card-title">Latest Signals</div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Symbol</th><th>Score</th><th>Rank</th></tr>
              </thead>
              <tbody>
                {[...signals].sort((a, b) => a.rank - b.rank).slice(0, 5).map((s) => (
                  <tr key={s.symbol}>
                    <td style={{ fontWeight: 600, color: "var(--color-accent)" }}>{s.symbol}</td>
                    <td>
                      <span style={{ fontVariantNumeric: "tabular-nums" }}>{s.score.toFixed(1)}</span>
                    </td>
                    <td style={{ color: "var(--color-text-muted)" }}>#{s.rank}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {!healthLoading && !error && !health && (
        <div className="state-banner state-empty">
          <div className="state-empty-icon">{"\u26A0"}</div>
          <div className="state-empty-title">Cannot connect to backend</div>
          <div className="state-empty-desc">
            Make sure the backend server is running on the configured API URL.
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
