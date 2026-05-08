import { useState } from "react";
import { ErrorMessage } from "../components/ErrorMessage";
import api from "../api/client";
import "./shared.css";

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

      {result?.checks && (
        <div className="card">
          <div className="card-title">Check Details</div>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Check</th><th>Status</th><th>Score</th></tr></thead>
              <tbody>
                {result.checks.map((c: any) => (
                  <tr key={c.id || c.name}>
                    <td style={{ fontWeight: 500 }}>{c.name}</td>
                    <td><span className={`badge ${c.result === "PASS" ? "badge-ok" : c.result === "WARN" ? "badge-warning" : "badge-error"}`}>{c.result}</span></td>
                    <td style={{ color: "var(--color-text-muted)", fontSize: "var(--text-sm)" }}>{c.detail}</td>
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
export default Audit;
