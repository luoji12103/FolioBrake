import { useState } from "react";
import { ErrorMessage } from "../components/ErrorMessage";
import api from "../api/client";
import "./shared.css";

const CHECK_DESCRIPTIONS: Record<string, string> = {
  leakage: "Verify no data leakage in backtest pipeline",
  walk_forward: "Walk-forward validation robustness",
  param_stability: "Parameter sensitivity & stability",
  cost_stress: "Transaction cost model stress test",
  regime_slicing: "Performance across market regimes",
  benchmark_comparison: "Risk-adjusted edge vs benchmark",
  turnover_feasibility: "Portfolio turnover feasibility",
};

function Audit() {
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRun = async () => {
    setLoading(true); setError(null);
    try {
      const { data } = await api.post("/audit/run", { strategy_config_id: 1, backtest_config_id: 1 });
      const res = await api.get(`/audit/report/${data.run_id}`);
      setResult(res.data);
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  const gradeColor: Record<string, string> = {
    GREEN: "var(--color-green)",
    YELLOW: "var(--color-yellow)",
    RED: "var(--color-red)",
  };

  const gradeGlow: Record<string, string> = {
    GREEN: "var(--shadow-glow-green)",
    YELLOW: "none",
    RED: "var(--shadow-glow-red)",
  };

  const scoreColor = (score: number) => {
    if (score >= 80) return "var(--color-green)";
    if (score >= 60) return "var(--color-yellow)";
    return "var(--color-red)";
  };

  return (
    <div className="page">
      <h2>Audit Gatekeeper</h2>
      <button className="btn-primary" onClick={handleRun} disabled={loading} style={{ marginBottom: "var(--space-4)" }}>
        {loading ? "Running..." : "Run Audit"}
      </button>

      {error && <ErrorMessage message={error} onRetry={handleRun} />}

      {!result && !loading && !error && (
        <div className="state-banner state-empty">
          <div className="state-empty-icon">{"\uD83D\uDD0D"}</div>
          <div className="state-empty-title">Validate your strategy</div>
          <div className="state-empty-desc">
            Run an audit to check strategy robustness, overfitting risk, and statistical significance.
          </div>
        </div>
      )}

      {result && (
        <div className="card" style={{ textAlign: "center", marginBottom: "var(--space-4)" }}>
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              width: 80,
              height: 80,
              borderRadius: "var(--radius-full)",
              background: `${gradeColor[result.grade] || "var(--color-text-dim)"}15`,
              border: `3px solid ${gradeColor[result.grade] || "var(--color-text-dim)"}`,
              margin: "0 auto var(--space-3)",
              boxShadow: gradeGlow[result.grade] || "none",
            }}
          >
            <span
              style={{
                fontSize: "var(--text-2xl)",
                fontWeight: 800,
                color: gradeColor[result.grade] || "var(--color-text-dim)",
              }}
            >
              {result.grade}
            </span>
          </div>
          <p style={{ color: "var(--color-text-muted)", fontSize: "var(--text-sm)", lineHeight: "var(--leading-relaxed)" }}>
            Score: <strong style={{ color: "var(--color-text)" }}>{result.score}</strong> {"\u2014"} {result.summary}
          </p>
        </div>
      )}

      {result?.score_breakdown && Object.keys(result.score_breakdown).length > 0 && (
        <div className="card">
          <div className="card-title">Score Breakdown</div>
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
            {Object.entries(result.score_breakdown).map(([cat, info]: [string, any]) => {
              const avgScore = info.total > 0 ? Math.round(info.score / info.total) : 0;
              return (
                <div key={cat}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "var(--space-1)" }}>
                    <span style={{ fontSize: "var(--text-sm)", fontWeight: 500, textTransform: "capitalize" }}>{cat}</span>
                    <span style={{ fontSize: "var(--text-xs)", color: "var(--color-text-muted)" }}>
                      {info.passed}/{info.total} passed {"\u00B7"} avg {avgScore}
                    </span>
                  </div>
                  <div style={{ height: 6, borderRadius: "var(--radius-full)", background: "var(--color-surface-raised)", overflow: "hidden" }}>
                    <div style={{ height: "100%", width: `${avgScore}%`, borderRadius: "var(--radius-full)", background: scoreColor(avgScore), transition: "width 0.4s var(--ease-out)" }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {result?.checks && (
        <div className="card">
          <div className="card-title">Check Details</div>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Check</th><th>Description</th><th>Status</th><th>Score</th></tr></thead>
              <tbody>
                {result.checks.map((c: any) => (
                  <tr key={c.id || c.name}>
                    <td style={{ fontWeight: 500 }}>{c.name}</td>
                    <td style={{ color: "var(--color-text-muted)", fontSize: "var(--text-xs)" }}>
                      {CHECK_DESCRIPTIONS[c.name] || c.category}
                    </td>
                    <td><span className={`badge ${c.status === "PASS" ? "badge-ok" : c.status === "WARN" ? "badge-warning" : "badge-error"}`}>{c.status}</span></td>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
                        <div style={{ flex: 1, height: 4, borderRadius: "var(--radius-full)", background: "var(--color-surface-raised)", overflow: "hidden", minWidth: 60 }}>
                          <div style={{ height: "100%", width: `${c.score}%`, borderRadius: "var(--radius-full)", background: scoreColor(c.score), transition: "width 0.4s var(--ease-out)" }} />
                        </div>
                        <span style={{ fontSize: "var(--text-xs)", color: scoreColor(c.score), fontWeight: 600, minWidth: 28, textAlign: "right" }}>{c.score}</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {result?.grade_history && result.grade_history.length > 1 && (
        <div className="card">
          <div className="card-title">Grade Trend</div>
          <div style={{ display: "flex", alignItems: "flex-end", gap: "var(--space-2)", height: 100 }}>
            {result.grade_history.map((h: any) => (
              <div key={h.id} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: "var(--space-1)" }}>
                <span style={{ fontSize: "var(--text-xs)", color: "var(--color-text-muted)" }}>{h.score}</span>
                <div style={{ width: "100%", borderRadius: "var(--radius-sm) var(--radius-sm) 0 0", background: gradeColor[h.grade] || "var(--color-text-dim)", height: `${h.score}%`, minHeight: 4, transition: "height 0.4s var(--ease-out)" }} />
                <span className={`badge badge-grade-${h.grade.toLowerCase()}`} style={{ fontSize: "9px", padding: "1px 4px" }}>{h.grade}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
export default Audit;
