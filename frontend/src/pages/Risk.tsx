import { useRiskState, useRiskRules, useRiskOverlay, RiskLevel } from "../api/hooks";
import { ErrorMessage } from "../components/ErrorMessage";
import RiskBadge from "../components/RiskBadge";
import "./shared.css";

/* ---- Severity badge ---- */

function SeverityBadge({ severity }: { severity: "INFO" | "WARNING" | "CRITICAL" }) {
  const map: Record<string, string> = {
    INFO: "badge-severity-info",
    WARNING: "badge-severity-warning",
    CRITICAL: "badge-severity-critical",
  };
  return (
    <span className={`badge ${map[severity]}`}>{severity}</span>
  );
}

/* ---- State machine ---- */

const STATE_FLOW: { level: RiskLevel; label: string; color: string }[] = [
  { level: "NORMAL", label: "Normal", color: "#34d399" },
  { level: "CAUTION", label: "Caution", color: "#fbbf24" },
  { level: "DEFENSIVE", label: "Defensive", color: "#f97316" },
  { level: "HALT", label: "Halt", color: "#f87171" },
];

function StateMachine({ active }: { active: RiskLevel }) {
  const activeIdx = STATE_FLOW.findIndex((s) => s.level === active);
  return (
    <div className="risk-statemachine">
      {STATE_FLOW.map((s, i) => {
        const isActive = s.level === active;
        const isPast = activeIdx >= 0 && i <= activeIdx;
        const showArrow = i < STATE_FLOW.length - 1;
        return (
          <div key={s.level} style={{ display: "flex", alignItems: "center" }}>
            <div className="risk-state-node">
              <div
                className={`risk-state-circle ${isActive ? "active" : ""}`}
                style={{
                  background: isPast ? s.color : "var(--color-surface)",
                  borderColor: isActive ? s.color : "var(--color-border)",
                  color: isPast ? "#0f1117" : "var(--color-text-muted)",
                }}
              >
                {isActive ? ">" : ""}
              </div>
              <span className="risk-state-label">{s.label}</span>
            </div>
            {showArrow && <div className="risk-state-arrow" />}
          </div>
        );
      })}
    </div>
  );
}

/* ---- Skeleton ---- */

function RiskSkeleton() {
  return (
    <div style={{ marginTop: 16 }}>
      <div className="skeleton" style={{ height: 48, width: 200, marginBottom: 20 }} />
      <div className="skeleton" style={{ height: 100, marginBottom: 20 }} />
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="skeleton-row">
          <div className="skeleton" />
          <div className="skeleton" />
          <div className="skeleton" />
          <div className="skeleton" />
        </div>
      ))}
    </div>
  );
}

/* ---- Page ---- */

function Risk() {
  const { data: riskState, error: stateErr, isLoading: stateLoading, refetch: refetchRisk } = useRiskState();
  const { data: rules, error: rulesErr, isLoading: rulesLoading } = useRiskRules();
  const { data: overlay, error: overlayErr, isLoading: overlayLoading } =
    useRiskOverlay();

  const isLoading = stateLoading || rulesLoading || overlayLoading;
  const error = stateErr || rulesErr || overlayErr;

  return (
    <div className="page">
      <h2>Risk Overlay</h2>

      {isLoading && <RiskSkeleton />}

      {error && <ErrorMessage message={`Failed to load risk data: ${error}`} onRetry={refetchRisk} />}

      {!isLoading && !error && !riskState && (
        <div className="state-banner state-empty">
          No risk data available.
        </div>
      )}

      {!isLoading && !error && riskState && (
        <>
          {/* ---- Large state indicator ---- */}
          <div className="card" style={{ textAlign: "center", padding: 32 }}>
            <p
              style={{
                fontSize: 14,
                color: "var(--color-text-muted)",
                marginBottom: 12,
                textTransform: "uppercase",
                letterSpacing: "0.05em",
              }}
            >
              Current Risk State
            </p>
            <div style={{ display: "flex", justifyContent: "center" }}>
              <span
                style={{
                  fontSize: 18,
                  padding: "10px 28px",
                  borderRadius: 99,
                  fontWeight: 700,
                  display: "inline-block",
                }}
              >
                <RiskBadge state={riskState.state} />
              </span>
            </div>
            <p
              style={{
                marginTop: 16,
                fontSize: 15,
                color: "var(--color-text)",
                maxWidth: 600,
                marginLeft: "auto",
                marginRight: "auto",
              }}
            >
              {riskState.transition_reason}
            </p>
          </div>

          {/* ---- State machine ---- */}
          <div className="card">
            <div className="card-title">State Machine</div>
            <StateMachine active={riskState.state} />
          </div>

          {/* ---- Triggered rules ---- */}
          <div className="card">
            <div className="card-title">Triggered Rules</div>
            {rules && rules.length > 0 ? (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Rule Name</th>
                      <th>Severity</th>
                      <th>Detail</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rules.map((r) => (
                      <tr key={r.rule_name}>
                        <td>{new Date(r.date).toLocaleDateString("en-CN")}</td>
                        <td style={{ fontWeight: 600 }}>{r.rule_name}</td>
                        <td>
                          <SeverityBadge severity={r.severity} />
                        </td>
                        <td style={{ whiteSpace: "normal", maxWidth: 240, fontSize: 13 }}>
                          {JSON.stringify(r.detail)}
                        </td>
                        <td>
                          <span
                            className={`badge ${r.triggered ? "badge-fail" : "badge-pass"}`}
                          >
                            {r.triggered ? "TRIGGERED" : "OK"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p style={{ color: "var(--color-text-muted)", fontSize: 14 }}>
                No rules triggered today.
              </p>
            )}
          </div>

          {/* ---- Overlay decision ---- */}
          <div className="card">
            <div className="card-title">Overlay Decision</div>
            {overlay ? (
              <>
                <p
                  style={{
                    fontSize: 15,
                    fontWeight: 600,
                    color: "var(--color-text)",
                    marginBottom: 8,
                  }}
                >
                  {overlay.decision}
                </p>
                <p
                  style={{
                    fontSize: 14,
                    color: "var(--color-text-muted)",
                    whiteSpace: "pre-wrap",
                  }}
                >
                  {overlay.reason}
                </p>
              </>
            ) : (
              <p style={{ color: "var(--color-text-muted)", fontSize: 14 }}>
                No overlay decision available.
              </p>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export default Risk;
