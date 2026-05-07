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

  const gradeColor = { GREEN: "#34d399", YELLOW: "#fbbf24", RED: "#f87171" } as const;

  return (
    <div className="page">
      <h2>Audit Gatekeeper</h2>
      <button className="btn-primary" onClick={handleRun} disabled={loading} style={{marginBottom:16}}>
        {loading ? "Running..." : "Run Audit"}
      </button>

      {error && <ErrorMessage message={error} onRetry={handleRun} />}
      {!result && !loading && !error && <div className="state-banner state-empty">Run an audit to validate strategy robustness.</div>}

      {result && (
        <div className="card" style={{textAlign:"center", marginBottom:16}}>
          <h3 style={{fontSize:32, color: gradeColor[result.grade as keyof typeof gradeColor] || "#8b8fa3"}}>
            {result.grade}
          </h3>
          <p style={{color:"var(--color-text-muted)"}}>Score: {result.score} — {result.summary}</p>
        </div>
      )}

      {result?.checks && (
        <div className="card">
          <h3>Check Details</h3>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Check</th><th>Status</th><th>Score</th></tr></thead>
              <tbody>
                {result.checks.map((c: any) => (
                  <tr key={c.id || c.name}>
                    <td>{c.name}</td>
                    <td><span className={`badge ${c.result === "PASS" ? "badge-ok" : c.result === "WARN" ? "badge-warning" : "badge-error"}`}>{c.result}</span></td>
                    <td>{c.detail}</td>
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
