import { useState, useMemo } from "react";
import api from "../api/client";
import { useSignals, usePortfolio, Signal } from "../api/hooks";
import { WeightBarChart } from "../components/Charts";
import { ErrorMessage } from "../components/ErrorMessage";
import "./shared.css";

function ScoreBar({ score, maxScore = 100 }: { score: number; maxScore?: number }) {
  const pct = Math.min(100, Math.max(0, (score / maxScore) * 100));
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <div
        style={{
          flex: 1, height: 6, borderRadius: 3,
          background: "var(--color-border)", overflow: "hidden", maxWidth: 80,
        }}
      >
        <div
          style={{
            width: `${pct}%`, height: "100%", borderRadius: 3,
            background: pct > 70 ? "var(--color-green)" : pct > 40 ? "var(--color-yellow)" : "var(--color-red)",
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

function SignalSkeleton() {
  return (
    <div style={{ marginTop: 16 }}>
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
        <span style={{ fontSize: 14, color: "var(--color-text)" }}>
          {signal.symbol} — Score: {signal.score.toFixed(1)} | Rank: #{signal.rank}
        </span>
      </div>
      {open && (
        <div className="expandable-body">
          <p style={{ fontSize: 13, color: "var(--color-text-muted)" }}>
            {formatReason(signal.reason)}
          </p>
          {signal.reason?.breakdown && (
            <div style={{ marginTop: 8 }}>
              {Object.entries(signal.reason.breakdown).map(([cat, info]: [string, any]) => (
                <div key={cat} style={{ display: "flex", justifyContent: "space-between", fontSize: 12, padding: "2px 0" }}>
                  <span>{cat}</span>
                  <span>weight: {info?.weight?.toFixed(2) || "?"}, sub: {info?.sub_score?.toFixed(3) || "?"}</span>
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
              <td style={{ fontWeight: 600 }}>{s.symbol}</td>
              <td><ScoreBar score={s.score} /></td>
              <td>#{s.rank}</td>
              <td style={{ maxWidth: 300, whiteSpace: "normal", fontSize: 12, color: "var(--color-text-muted)" }}>
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
    <div style={{ marginTop: 20 }}>
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
          No signals generated yet. Run a strategy evaluation to produce signals.
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
          <div style={{ marginTop: 16 }}>
            <h3 className="section-title">Paper Trading</h3>
            <div className="card" style={{ display: "flex", alignItems: "center", gap: 16 }}>
              <button className="btn-primary" onClick={handleCreateAndApply} disabled={applying}>
                {applying ? "Applying..." : (paperId ? `Apply to Portfolio #${paperId}` : "Create & Apply")}
              </button>
              <span style={{ fontSize: 13, color: applyMsg?.startsWith("Error") ? "var(--color-red)" : "var(--color-green)" }}>
                {applyMsg}
              </span>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default Signals;
