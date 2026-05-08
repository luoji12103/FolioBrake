import { useState, useMemo } from "react";
import api from "../api/client";
import { useSignals, usePortfolio, Signal } from "../api/hooks";
import { WeightBarChart } from "../components/Charts";
import { ErrorMessage } from "../components/ErrorMessage";
import "./shared.css";

function ScoreBar({ score, maxScore = 100 }: { score: number; maxScore?: number }) {
  const pct = Math.min(100, Math.max(0, (score / maxScore) * 100));
  const color = pct > 70 ? "var(--color-green)" : pct > 40 ? "var(--color-yellow)" : "var(--color-red)";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
      <div
        style={{
          flex: 1, height: 6, borderRadius: "var(--radius-full)",
          background: "var(--color-border)", overflow: "hidden", maxWidth: 80,
        }}
      >
        <div
          style={{
            width: `${pct}%`, height: "100%", borderRadius: "var(--radius-full)",
            background: color,
            transition: "width 0.4s var(--ease-out)",
            boxShadow: `0 0 8px ${color}40`,
          }}
        />
      </div>
      <span style={{ fontSize: "var(--text-sm)", fontWeight: 600, color: "var(--color-text)", fontVariantNumeric: "tabular-nums", minWidth: 32 }}>
        {score.toFixed(1)}
      </span>
    </div>
  );
}

function SignalSkeleton() {
  return (
    <div style={{ marginTop: "var(--space-4)" }}>
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="skeleton-row">
          <div className="skeleton" /><div className="skeleton" /><div className="skeleton" />
          <div className="skeleton" /><div className="skeleton" />
        </div>
      ))}
    </div>
  );
}

function formatReason(reason: Record<string, any>): string {
  if (!reason || !reason.breakdown) return "N/A";
  const bd = reason.breakdown;
  return Object.entries(bd)
    .map(([cat, info]: [string, any]) => `${cat}: ${info?.sub_score?.toFixed(2) || "0"}`)
    .join(", ");
}

function SignalExpandable({ signal }: { signal: Signal }) {
  const [open, setOpen] = useState(false);
  return (
    <div>
      <div className="expandable-header" onClick={() => setOpen(!open)} role="button" tabIndex={0}
        aria-expanded={open} onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") setOpen(!open); }}>
        <span className={`expandable-arrow ${open ? "open" : ""}`}>&#9654;</span>
        <span style={{ fontSize: "var(--text-base)", color: "var(--color-text)" }}>
          <span style={{ color: "var(--color-accent)", fontWeight: 600 }}>{signal.symbol}</span>
          <span style={{ color: "var(--color-text-dim)", margin: "0 6px" }}>{"\u2014"}</span>
          <span style={{ color: "var(--color-text-muted)" }}>Score: {signal.score.toFixed(1)}</span>
          <span style={{ color: "var(--color-text-dim)", margin: "0 4px" }}>{"\u00B7"}</span>
          <span style={{ color: "var(--color-text-muted)" }}>Rank: #{signal.rank}</span>
        </span>
      </div>
      {open && (
        <div className="expandable-body">
          <p style={{ fontSize: "var(--text-sm)", color: "var(--color-text-muted)" }}>
            {formatReason(signal.reason)}
          </p>
          {signal.reason?.breakdown && (
            <div style={{ marginTop: "var(--space-2)" }}>
              {Object.entries(signal.reason.breakdown).map(([cat, info]: [string, any]) => (
                <div key={cat} style={{ display: "flex", justifyContent: "space-between", fontSize: "var(--text-xs)", padding: "2px 0", color: "var(--color-text-dim)" }}>
                  <span>{cat}</span>
                  <span style={{ fontVariantNumeric: "tabular-nums" }}>weight: {info?.weight?.toFixed(2) || "?"}, sub: {info?.sub_score?.toFixed(3) || "?"}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function SignalsTable({ signals }: { signals: Signal[] }) {
  const sorted = useMemo(() => [...signals].sort((a, b) => a.rank - b.rank), [signals]);

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Score</th>
            <th>Rank</th>
            <th>Reason</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((s) => (
            <tr key={s.symbol}>
              <td style={{ fontWeight: 600, color: "var(--color-accent)" }}>{s.symbol}</td>
              <td><ScoreBar score={s.score} /></td>
              <td style={{ color: "var(--color-text-muted)", fontVariantNumeric: "tabular-nums" }}>#{s.rank}</td>
              <td style={{ maxWidth: 300, whiteSpace: "normal", fontSize: "var(--text-xs)", color: "var(--color-text-dim)" }}>
                {formatReason(s.reason)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SignalDetails({ signals }: { signals: Signal[] }) {
  const sorted = useMemo(() => [...signals].sort((a, b) => a.rank - b.rank), [signals]);
  return (
    <div style={{ marginTop: "var(--space-6)" }}>
      <h3 className="section-title">Signal Explanations</h3>
      <div className="card">
        {sorted.map((s) => <SignalExpandable key={s.symbol} signal={s} />)}
      </div>
    </div>
  );
}

function Signals() {
  const { data: signals, error, isLoading, refetch } = useSignals();
  const { data: portfolio, isLoading: portfolioLoading, error: portfolioError } = usePortfolio();
  const [paperId, setPaperId] = useState<number | null>(null);
  const [applying, setApplying] = useState(false);
  const [applyMsg, setApplyMsg] = useState<string | null>(null);

  const handleCreateAndApply = async () => {
    setApplying(true); setApplyMsg(null);
    try {
      let pid = paperId;
      if (!pid) {
        const { data } = await api.post("/paper/portfolio", { name: "default", initial_capital: 100000 });
        pid = data.portfolio_id;
        setPaperId(pid);
      }
      if (!portfolio || portfolio.length === 0) {
        setApplyMsg("No portfolio weights to apply.");
        return;
      }
      const weights: Record<string, number> = {};
      portfolio.forEach((p: any) => { weights[String(p.instrument_id)] = p.target_weight; });
      const today = new Date().toISOString().slice(0, 10);
      await api.post("/paper/apply-signal", { portfolio_id: pid, signal_date: today, target_weights: weights });
      setApplyMsg(`Applied ${portfolio.length} positions to paper portfolio #${pid}.`);
    } catch (e: any) {
      setApplyMsg(`Error: ${e?.response?.data?.detail || e.message}`);
    } finally { setApplying(false); }
  };

  return (
    <div className="page">
      <h2>Weekly Signals</h2>

      {isLoading && <SignalSkeleton />}

      {error && <ErrorMessage message={`Failed to load signals: ${error}`} onRetry={refetch} />}

      {!isLoading && !error && signals && signals.length === 0 && (
        <div className="state-banner state-empty">
          <div className="state-empty-icon">{"\uD83D\uDCC8"}</div>
          <div className="state-empty-title">No signals generated yet</div>
          <div className="state-empty-desc">
            Run a strategy evaluation to produce weekly trading signals.
          </div>
        </div>
      )}

      {!isLoading && !error && signals && signals.length > 0 && (
        <>
          <div className="card"><SignalsTable signals={signals} /></div>
          <SignalDetails signals={signals} />
        </>
      )}

      {!portfolioLoading && !portfolioError && portfolio && portfolio.length > 0 && (
        <>
          <div style={{ marginTop: "var(--space-8)" }}>
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
          <div style={{ marginTop: "var(--space-4)" }}>
            <h3 className="section-title">Paper Trading</h3>
            <div className="card" style={{ display: "flex", alignItems: "center", gap: "var(--space-4)" }}>
              <button className="btn-primary" onClick={handleCreateAndApply} disabled={applying}>
                {applying ? "Applying..." : (paperId ? `Apply to Portfolio #${paperId}` : "Create & Apply")}
              </button>
              {applyMsg && (
                <span className={`toast ${applyMsg.startsWith("Error") ? "toast-error" : "toast-success"}`}>
                  {applyMsg}
                </span>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default Signals;
