import { useEffect, useState } from "react";
import { healthCheck } from "../api/client";
import {
  useRiskState,
  useSignals,
  usePortfolio,
  usePaperPortfolios,
  usePaperPerformance,
  usePaperPnl,
  useRealtimePrices,
  Signal,
} from "../api/hooks";
import { EquityChart, DrawdownChart } from "../components/Charts";
import { ErrorMessage } from "../components/ErrorMessage";
import { DataTable, type ColumnDef } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import "./shared.css";

function DashboardSkeleton() {
  return (
    <div className="stat-grid">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="skeleton-card">
          <div className="skeleton" style={{ width: "40%", height: 12 }} />
          <div className="skeleton" style={{ width: "65%", height: 28 }} />
        </div>
      ))}
    </div>
  );
}

const DASHBOARD_SIGNAL_COLUMNS: ColumnDef<Signal>[] = [
  {
    key: "symbol",
    label: "Symbol",
    sortable: true,
    render: (v) => <span style={{ fontWeight: 600, color: "var(--color-accent)" }}>{String(v)}</span>,
  },
  {
    key: "score",
    label: "Score",
    sortable: true,
    render: (v) => <span style={{ fontVariantNumeric: "tabular-nums" }}>{(v as number).toFixed(1)}</span>,
  },
  {
    key: "rank",
    label: "Rank",
    sortable: true,
    render: (v) => <span style={{ color: "var(--color-text-muted)" }}>#{String(v)}</span>,
  },
];

const RISK_BADGE_CLASS: Record<string, string> = {
  NORMAL: "normal",
  CAUTION: "caution",
  DEFENSIVE: "defensive",
  HALT: "halt",
};

const RISK_COLOR: Record<string, string> = {
  NORMAL: "var(--color-green)",
  CAUTION: "var(--color-yellow)",
  DEFENSIVE: "var(--color-orange)",
  HALT: "var(--color-red)",
};

function formatCurrency(value: number): string {
  if (Math.abs(value) >= 1_000_000) {
    return `$${(value / 1_000_000).toFixed(2)}M`;
  }
  if (Math.abs(value) >= 1_000) {
    return `$${(value / 1_000).toFixed(1)}K`;
  }
  return `$${value.toFixed(2)}`;
}

function Dashboard() {
  const [health, setHealth] = useState<{ status: string; version: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [healthLoading, setHealthLoading] = useState(true);
  const { data: riskState } = useRiskState();
  const { data: signals } = useSignals();
  const { data: portfolio } = usePortfolio();
  const { data: portfolios } = usePaperPortfolios();
  const { data: pnl } = usePaperPnl(portfolios?.[0]?.id?.toString() || null);
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

  const currentState = riskState?.state || "NORMAL";
  const now = new Date();
  const greeting = now.getHours() < 12 ? "Good morning" : now.getHours() < 18 ? "Good afternoon" : "Good evening";

  return (
    <div className="page">
      {error && <ErrorMessage message={`Backend offline: ${error}`} onRetry={fetchHealth} />}

      {health && (
        <>
          <div className="dashboard-header">
            <div className="dashboard-header-left">
              <h2 className="dashboard-title">{greeting}</h2>
              <div className="dashboard-subtitle">
                <span>{now.toLocaleDateString("en-US", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}</span>
                <span style={{ color: "var(--color-text-dim)" }}>·</span>
                <span className={`risk-badge ${RISK_BADGE_CLASS[currentState] || "normal"}`}>
                  <span style={{
                    display: "inline-block",
                    width: 6,
                    height: 6,
                    borderRadius: "50%",
                    backgroundColor: RISK_COLOR[currentState],
                  }} />
                  {currentState}
                </span>
                {wsConnected && (
                  <span style={{ display: "inline-flex", alignItems: "center", gap: 4, color: "var(--color-text-dim)", fontSize: "var(--text-xs)" }}>
                    <span style={{
                      display: "inline-block",
                      width: 6,
                      height: 6,
                      borderRadius: "50%",
                      backgroundColor: "var(--color-green)",
                      animation: "badgePulse 2s infinite",
                    }} />
                    Live
                  </span>
                )}
              </div>
            </div>
            <div className="dashboard-header-right">
              <button className="btn-secondary" onClick={() => window.location.href = "/signals"}>View Signals</button>
              <button className="btn-primary" onClick={() => window.location.href = "/paper"}>Portfolio</button>
            </div>
          </div>

          <div className="stat-grid">
            <div className="stat-card">
              <div className="stat-label">
                <span style={{ fontSize: 14 }}>📊</span>
                Total Value
              </div>
              <div className="stat-value">
                {pnl ? formatCurrency(pnl.total_value) : "\u2014"}
              </div>
              {pnl && (
                <div className={`stat-trend ${pnl.total_pnl >= 0 ? "positive" : "negative"}`}>
                  <span>{pnl.total_pnl >= 0 ? "↑" : "↓"}</span>
                  {Math.abs(pnl.total_pnl_pct).toFixed(2)}%
                </div>
              )}
              {pnl && (
                <div className="stat-footer">
                  Cash: {formatCurrency(pnl.cash)} · Invested: {formatCurrency(pnl.invested)}
                </div>
              )}
            </div>

            <div className="stat-card">
              <div className="stat-label">
                <span style={{ fontSize: 14 }}>💰</span>
                P&L
              </div>
              <div className="stat-value" style={{ color: pnl ? (pnl.total_pnl >= 0 ? "var(--color-green)" : "var(--color-red)") : "var(--color-text)" }}>
                {pnl ? `${pnl.total_pnl >= 0 ? "+" : ""}${formatCurrency(pnl.total_pnl)}` : "\u2014"}
              </div>
              {pnl && (
                <div className={`stat-trend ${pnl.total_pnl >= 0 ? "positive" : "negative"}`}>
                  <span>{pnl.total_pnl >= 0 ? "↑" : "↓"}</span>
                  {pnl.total_pnl >= 0 ? "Gaining" : "Losing"}
                </div>
              )}
              <div className="stat-footer">Paper portfolio performance</div>
            </div>

            <div className="stat-card">
              <div className="stat-label">
                <span style={{ fontSize: 14 }}>📡</span>
                Active Signals
              </div>
              <div className="stat-value">
                {signals ? signals.length : "\u2014"}
              </div>
              {topSignal && (
                <div className="stat-trend neutral">
                  Top: {topSignal.symbol} ({topSignal.score.toFixed(1)})
                </div>
              )}
              <div className="stat-footer">
                {portfolio ? `${portfolio.length} ETFs tracked` : "Loading portfolio..."}
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-label">
                <span style={{ fontSize: 14 }}>🛡️</span>
                Risk Level
              </div>
              <div className="stat-value" style={{ color: RISK_COLOR[currentState] }}>
                {currentState}
              </div>
              <div className={`stat-trend ${currentState === "NORMAL" ? "positive" : currentState === "HALT" ? "negative" : "neutral"}`}>
                {currentState === "NORMAL" ? "All clear" : currentState === "CAUTION" ? "Monitoring" : currentState === "DEFENSIVE" ? "Defensive mode" : "Trading halted"}
              </div>
              <div className="stat-footer">Next rebalance: Friday</div>
            </div>
          </div>

          <div className="quick-actions">
            <a href="/signals" className="quick-action">
              <div className="quick-action-icon">📡</div>
              <div className="quick-action-text">
                <span className="quick-action-label">Signals</span>
                <span className="quick-action-desc">View ranked signals</span>
              </div>
            </a>
            <a href="/paper" className="quick-action">
              <div className="quick-action-icon">📈</div>
              <div className="quick-action-text">
                <span className="quick-action-label">Paper Trading</span>
                <span className="quick-action-desc">Manage portfolios</span>
              </div>
            </a>
            <a href="/risk" className="quick-action">
              <div className="quick-action-icon">🛡️</div>
              <div className="quick-action-text">
                <span className="quick-action-label">Risk Controls</span>
                <span className="quick-action-desc">Rules & overlays</span>
              </div>
            </a>
            <a href="/backtest" className="quick-action">
              <div className="quick-action-icon">🧪</div>
              <div className="quick-action-text">
                <span className="quick-action-label">Backtest</span>
                <span className="quick-action-desc">Run strategies</span>
              </div>
            </a>
          </div>

          <div className="dashboard-grid">
            <div className="dashboard-grid-main">
              {performance && performance.equity_curve.length > 0 && (
                <div className="card">
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

              {!performance && (
                <div className="card">
                  <div className="card-title">Portfolio Performance</div>
                  <EmptyState
                    icon="📊"
                    title="No performance data"
                    description="Start a paper portfolio from the Signals page to track performance over time."
                  />
                </div>
              )}

              {signals && signals.length > 0 && (
                <div className="card">
                  <div className="card-title">Latest Signals</div>
                  <DataTable
                    data={[...signals].sort((a, b) => a.rank - b.rank).slice(0, 5) as unknown as Record<string, unknown>[]}
                    columns={DASHBOARD_SIGNAL_COLUMNS as unknown as ColumnDef<Record<string, unknown>>[]}
                    showFilter={false}
                    showPagination={false}
                  />
                </div>
              )}

              {signals && signals.length === 0 && (
                <div className="card">
                  <div className="card-title">Latest Signals</div>
                  <EmptyState
                    icon="📡"
                    title="No signals yet"
                    description="Signals are generated weekly by the strategy engine. Check back after the next evaluation run."
                  />
                </div>
              )}
            </div>

            <div className="dashboard-grid-side">
              <div className="timeline-card">
                <div className="timeline-header">
                  <div className="timeline-title">Recent Activity</div>
                </div>
                <div className="timeline-list">
                  {topSignal && (
                    <div className="timeline-item">
                      <div className="timeline-dot" />
                      <div className="timeline-content">
                        <div className="timeline-text">
                          Top signal: <strong style={{ color: "var(--color-accent)" }}>{topSignal.symbol}</strong> scored {topSignal.score.toFixed(1)}
                        </div>
                        <div className="timeline-meta">Latest signal update</div>
                      </div>
                    </div>
                  )}
                  {pnl && (
                    <div className="timeline-item">
                      <div className="timeline-dot" style={{ background: pnl.total_pnl >= 0 ? "var(--color-green)" : "var(--color-red)" }} />
                      <div className="timeline-content">
                        <div className="timeline-text">
                          Portfolio {pnl.total_pnl >= 0 ? "up" : "down"} <strong>{Math.abs(pnl.total_pnl_pct).toFixed(2)}%</strong>
                        </div>
                        <div className="timeline-meta">P&L: {formatCurrency(pnl.total_pnl)}</div>
                      </div>
                    </div>
                  )}
                  <div className="timeline-item">
                    <div className="timeline-dot" style={{ background: RISK_COLOR[currentState] }} />
                    <div className="timeline-content">
                      <div className="timeline-text">
                        Risk state: <strong style={{ color: RISK_COLOR[currentState] }}>{currentState}</strong>
                      </div>
                      <div className="timeline-meta">Current market regime</div>
                    </div>
                  </div>
                  {priceUpdate && (
                    <div className="timeline-item">
                      <div className="timeline-dot" style={{ background: priceUpdate.change >= 0 ? "var(--color-green)" : "var(--color-red)" }} />
                      <div className="timeline-content">
                        <div className="timeline-text">
                          <strong style={{ color: "var(--color-accent)" }}>{priceUpdate.symbol}</strong> at {priceUpdate.price.toFixed(3)}
                          <span style={{ color: priceUpdate.change >= 0 ? "var(--color-green)" : "var(--color-red)", marginLeft: 6 }}>
                            {priceUpdate.change >= 0 ? "+" : ""}{priceUpdate.change_pct.toFixed(2)}%
                          </span>
                        </div>
                        <div className="timeline-meta">Live price update</div>
                      </div>
                    </div>
                  )}
                  {health && (
                    <div className="timeline-item">
                      <div className="timeline-dot" style={{ background: "var(--color-text-dim)" }} />
                      <div className="timeline-content">
                        <div className="timeline-text">System healthy</div>
                        <div className="timeline-meta">v{health.version}</div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </>
      )}

      {healthLoading && <DashboardSkeleton />}

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
