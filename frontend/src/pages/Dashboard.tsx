import { useEffect, useState } from "react";
import { healthCheck } from "../api/client";
import { useRiskState, useSignals, usePortfolio } from "../api/hooks";
import { ErrorMessage } from "../components/ErrorMessage";
import "./shared.css";

function Dashboard() {
  const [health, setHealth] = useState<{ status: string; version: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { data: riskState } = useRiskState();
  const { data: signals } = useSignals();
  const { data: portfolio } = usePortfolio();

  const fetchHealth = () => {
    setError(null);
    healthCheck().then(setHealth).catch((err) => setError(err.message));
  };

  useEffect(() => { fetchHealth(); }, []);

  const topSignal = signals && signals.length > 0
    ? [...signals].sort((a, b) => b.score - a.score)[0]
    : null;

  return (
    <div className="page">
      <h2>Dashboard</h2>

      {error && <ErrorMessage message={`Backend offline: ${error}`} onRetry={fetchHealth} />}

      {health && (
        <div className="metric-grid" style={{ marginBottom: 24 }}>
          <div className="metric-card">
            <div className="metric-label">Risk State</div>
            <div className="metric-value">{riskState?.state || "NORMAL"}</div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Portfolio</div>
            <div className="metric-value">{portfolio ? `${portfolio.length} ETFs` : "—"}</div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Top Signal</div>
            <div className="metric-value" style={{ fontSize: 20 }}>
              {topSignal ? `${topSignal.symbol} (${topSignal.score.toFixed(1)})` : "—"}
            </div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Next Rebalance</div>
            <div className="metric-value" style={{ fontSize: 20 }}>Friday</div>
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
                    <td style={{ fontWeight: 600 }}>{s.symbol}</td>
                    <td>{s.score.toFixed(1)}</td>
                    <td>#{s.rank}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
