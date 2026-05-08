import { useRiskState, useRiskRules, useRiskOverlay, RiskLevel, RiskRule } from "../api/hooks";
import { ErrorMessage } from "../components/ErrorMessage";
import { DataTable, type ColumnDef } from "../components/DataTable";
import RiskBadge from "../components/RiskBadge";
import "./shared.css";

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

const STATE_FLOW: { level: RiskLevel; label: string; color: string }[] = [
  { level: "NORMAL", label: "Normal", color: "var(--color-green)" },
  { level: "CAUTION", label: "Caution", color: "var(--color-yellow)" },
  { level: "DEFENSIVE", label: "Defensive", color: "var(--color-orange)" },
  { level: "HALT", label: "Halt", color: "var(--color-red)" },
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
                  background: isPast ? s.color : "var(--color-surface-raised)",
                  borderColor: isActive ? s.color : "var(--color-border)",
                  color: isPast ? "#0a0c14" : "var(--color-text-dim)",
                  boxShadow: isActive ? `0 0 20px ${s.color}30` : "none",
                }}
              >
                {isActive ? "\u2713" : ""}
              </div>
              <span className="risk-state-label" style={{ color: isActive ? s.color : undefined }}>
                {s.label}
              </span>
            </div>
            {showArrow && <div className="risk-state-arrow" />}
          </div>
        );
      })}
    </div>
  );
}

function RiskSkeleton() {
  return (
    <div style={{ marginTop: "var(--space-4)" }}>
      <div className="skeleton-card">
        <div className="skeleton" style={{ height: 12, width: "30%" }} />
        <div className="skeleton" style={{ height: 40, width: "50%" }} />
      </div>
      <div className="skeleton" style={{ height: 100, marginBottom: "var(--space-5)", borderRadius: "var(--radius-lg)" }} />
      {Array.from({ length: 4 }).map((_, i) => (
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

const RULE_COLUMNS: ColumnDef<RiskRule>[] = [
  {
    key: "date",
    label: "Date",
    sortable: true,
    render: (v) => (
      <span style={{ color: "var(--color-text-dim)", fontSize: "var(--text-xs)" }}>
        {new Date(v as string).toLocaleDateString("en-CN")}
      </span>
    ),
  },
  {
    key: "rule_name",
    label: "Rule Name",
    sortable: true,
    render: (v) => <span style={{ fontWeight: 600 }}>{String(v)}</span>,
  },
  {
    key: "severity",
    label: "Severity",
    sortable: true,
    render: (v) => <SeverityBadge severity={v as "INFO" | "WARNING" | "CRITICAL"} />,
  },
  {
    key: "detail",
    label: "Detail",
    render: (v) => (
      <span style={{ whiteSpace: "normal", maxWidth: 240, fontSize: "var(--text-xs)", color: "var(--color-text-dim)", display: "inline-block" }}>
        {JSON.stringify(v)}
      </span>
    ),
  },
  {
    key: "triggered",
    label: "Status",
    sortable: true,
    render: (v) => (
      <span className={`badge ${(v as boolean) ? "badge-fail" : "badge-pass"}`}>
        {(v as boolean) ? "TRIGGERED" : "OK"}
      </span>
    ),
  },
];

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
          <div className="state-empty-icon">{"\uD83D\uDEE1"}</div>
          <div className="state-empty-title">No risk data available</div>
          <div className="state-empty-desc">
            Risk overlay data will appear here once the risk engine is running.
          </div>
        </div>
      )}

      {!isLoading && !error && riskState && (
        <>
          <div className="card" style={{ textAlign: "center", padding: "var(--space-8)" }}>
            <p
              style={{
                fontSize: "var(--text-xs)",
                color: "var(--color-text-dim)",
                marginBottom: "var(--space-3)",
                textTransform: "uppercase",
                letterSpacing: "var(--tracking-wider)",
                fontWeight: 600,
              }}
            >
              Current Risk State
            </p>
            <div style={{ display: "flex", justifyContent: "center" }}>
              <span
                style={{
                  fontSize: "var(--text-lg)",
                  padding: "10px 28px",
                  borderRadius: "var(--radius-full)",
                  fontWeight: 700,
                  display: "inline-block",
                }}
              >
                <RiskBadge state={riskState.state} />
              </span>
            </div>
            <p
              style={{
                marginTop: "var(--space-4)",
                fontSize: "var(--text-base)",
                color: "var(--color-text-muted)",
                maxWidth: 600,
                marginLeft: "auto",
                marginRight: "auto",
                lineHeight: "var(--leading-relaxed)",
              }}
            >
              {riskState.transition_reason}
            </p>
          </div>

          <div className="card">
            <div className="card-title">State Machine</div>
            <StateMachine active={riskState.state} />
          </div>

          <div className="card">
            <div className="card-title">Triggered Rules</div>
            {rules && rules.length > 0 ? (
              <DataTable
                data={rules as unknown as Record<string, unknown>[]}
                columns={RULE_COLUMNS as unknown as ColumnDef<Record<string, unknown>>[]}
                pageSize={15}
                showFilter={true}
                filterPlaceholder="Search rules\u2026"
              />
            ) : (
              <div className="state-banner state-empty" style={{ marginBottom: 0 }}>
                <div className="state-empty-icon">{"\u2705"}</div>
                <div className="state-empty-title">All clear</div>
                <div className="state-empty-desc">No rules triggered today.</div>
              </div>
            )}
          </div>

          <div className="card">
            <div className="card-title">Overlay Decision</div>
            {overlay ? (
              <>
                <p
                  style={{
                    fontSize: "var(--text-base)",
                    fontWeight: 600,
                    color: "var(--color-text)",
                    marginBottom: "var(--space-2)",
                  }}
                >
                  {overlay.decision}
                </p>
                <p
                  style={{
                    fontSize: "var(--text-sm)",
                    color: "var(--color-text-muted)",
                    whiteSpace: "pre-wrap",
                    lineHeight: "var(--leading-relaxed)",
                  }}
                >
                  {overlay.reason}
                </p>
              </>
            ) : (
              <p style={{ color: "var(--color-text-dim)", fontSize: "var(--text-sm)" }}>
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
