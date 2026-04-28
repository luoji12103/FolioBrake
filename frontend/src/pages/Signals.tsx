import { useState, useMemo } from "react";
import { useSignals, usePortfolio, Signal } from "../api/hooks";
import { WeightBarChart } from "../components/Charts";
import "./shared.css";

/* ---- Badge helpers ---- */

function ActionBadge({ action }: { action: Signal["action"] }) {
  const map: Record<string, string> = {
    BUY: "badge-buy",
    SELL: "badge-sell",
    HOLD: "badge-hold",
  };
  return (
    <span className={`badge ${map[action] || "badge-hold"}`}>{action}</span>
  );
}

function ScoreBar({ score, maxScore = 100 }: { score: number; maxScore?: number }) {
  const pct = Math.min(100, Math.max(0, (score / maxScore) * 100));
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <div
        style={{
          flex: 1,
          height: 6,
          borderRadius: 3,
          background: "var(--color-border)",
          overflow: "hidden",
          maxWidth: 80,
        }}
      >
        <div
          style={{
            width: `${pct}%`,
            height: "100%",
            borderRadius: 3,
            background:
              pct > 70
                ? "var(--color-green)"
                : pct > 40
                  ? "var(--color-yellow)"
                  : "var(--color-red)",
            transition: "width 0.3s ease",
          }}
        />
      </div>
      <span style={{ fontSize: 13, fontWeight: 600, color: "var(--color-text)" }}>
        {score.toFixed(1)}
      </span>
    </div>
  );
}

function WeightBar({ pct }: { pct: number }) {
  const width = Math.min(100, Math.max(0, pct * 100));
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <div className="weight-bar" style={{ flex: 1, maxWidth: 80 }}>
        <div className="weight-bar-fill" style={{ width: `${width}%` }} />
      </div>
      <span style={{ fontSize: 13, fontWeight: 600, color: "var(--color-text)" }}>
        {(pct * 100).toFixed(1)}%
      </span>
    </div>
  );
}

/* ---- Skeleton ---- */

function SignalSkeleton() {
  return (
    <div style={{ marginTop: 16 }}>
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="skeleton-row">
          <div className="skeleton" />
          <div className="skeleton" />
          <div className="skeleton" />
          <div className="skeleton" />
          <div className="skeleton" />
          <div className="skeleton" />
          <div className="skeleton" />
        </div>
      ))}
    </div>
  );
}

/* ---- Explanation accordion for a single signal ---- */

function SignalExpandable({ signal }: { signal: Signal }) {
  const [open, setOpen] = useState(false);
  return (
    <div>
      <div
        className="expandable-header"
        onClick={() => setOpen(!open)}
        role="button"
        tabIndex={0}
        aria-expanded={open}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") setOpen(!open);
        }}
      >
        <span className={`expandable-arrow ${open ? "open" : ""}`}>&#9654;</span>
        <span style={{ fontSize: 14, color: "var(--color-text)" }}>
          {signal.symbol} — {signal.name}
        </span>
      </div>
      {open && (
        <div className="expandable-body">
          <p>
            <strong>Score:</strong> {signal.score.toFixed(1)} |{" "}
            <strong>Rank:</strong> #{signal.rank} |{" "}
            <strong>Target Weight:</strong>{" "}
            {(signal.target_weight * 100).toFixed(1)}% |{" "}
            <strong>Action:</strong>{" "}
            <ActionBadge action={signal.action} />
          </p>
          <p style={{ marginTop: 8 }}>{signal.reason}</p>
        </div>
      )}
    </div>
  );
}

/* ---- Signals table ---- */

function SignalsTable({ signals }: { signals: Signal[] }) {
  const sorted = useMemo(
    () => [...signals].sort((a, b) => a.rank - b.rank),
    [signals]
  );

  const hasName = sorted.some((s) => s.name);
  const hasTargetWeight = sorted.some((s) => s.target_weight != null);
  const hasAction = sorted.some((s) => s.action);

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Symbol</th>
            {hasName && <th>Name</th>}
            <th>Score</th>
            <th>Rank</th>
            {hasTargetWeight && <th>Target Weight</th>}
            {hasAction && <th>Action</th>}
            <th>Reason</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((s) => (
            <tr key={s.symbol}>
              <td style={{ fontWeight: 600 }}>{s.symbol}</td>
              {hasName && <td>{s.name}</td>}
              <td>
                <ScoreBar score={s.score} />
              </td>
              <td>#{s.rank}</td>
              {hasTargetWeight && (
                <td>
                  <WeightBar pct={s.target_weight} />
                </td>
              )}
              {hasAction && (
                <td>
                  <ActionBadge action={s.action} />
                </td>
              )}
              <td style={{ maxWidth: 240, whiteSpace: "normal", fontSize: 13 }}>
                {s.reason}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ---- Expandable detail view for mobile / deep dive ---- */

function SignalDetails({ signals }: { signals: Signal[] }) {
  const sorted = useMemo(
    () => [...signals].sort((a, b) => a.rank - b.rank),
    [signals]
  );

  return (
    <div style={{ marginTop: 20 }}>
      <h3 className="section-title">Signal Explanations</h3>
      <div className="card">
        {sorted.map((s) => (
          <SignalExpandable key={s.symbol} signal={s} />
        ))}
      </div>
    </div>
  );
}

/* ---- Page ---- */

function Signals() {
  const { data: signals, error, isLoading } = useSignals();
  const { data: portfolio, isLoading: portfolioLoading, error: portfolioError } = usePortfolio();

  return (
    <div className="page">
      <h2>Weekly Signals</h2>

      {isLoading && <SignalSkeleton />}

      {error && (
        <div className="state-banner state-error">
          <span>Failed to load signals: {error}</span>
        </div>
      )}

      {!isLoading && !error && signals && signals.length === 0 && (
        <div className="state-banner state-empty">
          No signals generated yet. Run a strategy evaluation to produce signals.
        </div>
      )}

      {!isLoading && !error && signals && signals.length > 0 && (
        <>
          <div className="card">
            <SignalsTable signals={signals} />
          </div>
          <SignalDetails signals={signals} />
        </>
      )}

      {!portfolioLoading && !portfolioError && portfolio && portfolio.length > 0 && (
        <div style={{ marginTop: 32 }}>
          <h3 className="section-title">Portfolio Weights</h3>
          <div className="card">
            <WeightBarChart
              data={portfolio.map((p) => ({
                symbol: p.symbol,
                target_weight: p.target_weight * 100,
              }))}
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default Signals;
