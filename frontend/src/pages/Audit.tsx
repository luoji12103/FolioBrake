import { useState } from "react";
import {
  useAuditReport,
  useMutation,
  AuditCheck,
  CheckResult,
} from "../api/hooks";
import "./shared.css";

/* ---- Badge helpers ---- */

function CheckBadge({ result }: { result: CheckResult }) {
  const map: Record<CheckResult, string> = {
    PASS: "badge-pass",
    WARN: "badge-warn",
    FAIL: "badge-fail",
  };
  return (
    <span className={`badge ${map[result]}`}>{result}</span>
  );
}

function GradeBadge({ grade }: { grade: "GREEN" | "YELLOW" | "RED" }) {
  const map: Record<string, string> = {
    GREEN: "badge-grade-green",
    YELLOW: "badge-grade-yellow",
    RED: "badge-grade-red",
  };
  return (
    <span className={`badge ${map[grade]}`}>{grade}</span>
  );
}

/* ---- Expandable check row ---- */

function CheckRow({ check }: { check: AuditCheck }) {
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
        style={{ padding: "10px 0" }}
      >
        <span className={`expandable-arrow ${open ? "open" : ""}`}>&#9654;</span>
        <CheckBadge result={check.result} />
        <span
          style={{
            fontWeight: 600,
            fontSize: 14,
            color: "var(--color-text)",
            marginLeft: 8,
          }}
        >
          {check.name}
        </span>
        <span
          style={{
            fontSize: 12,
            color: "var(--color-text-muted)",
            marginLeft: "auto",
          }}
        >
          {check.category}
        </span>
      </div>
      {open && (
        <div className="expandable-body">
          <p style={{ marginBottom: 6 }}>
            <strong>Description:</strong> {check.description}
          </p>
          <p style={{ whiteSpace: "pre-wrap" }}>
            <strong>Detail:</strong> {check.detail}
          </p>
        </div>
      )}
    </div>
  );
}

/* ---- Skeleton ---- */

function AuditSkeleton() {
  return (
    <div style={{ marginTop: 16 }}>
      <div className="skeleton" style={{ height: 80, width: 200, marginBottom: 20 }} />
      <div className="skeleton" style={{ height: 40, width: 300, marginBottom: 20 }} />
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="skeleton-row">
          <div className="skeleton" />
          <div className="skeleton" />
          <div className="skeleton" />
        </div>
      ))}
    </div>
  );
}

/* ---- Check summary ---- */

function CheckSummary({ checks }: { checks: AuditCheck[] }) {
  const pass = checks.filter((c) => c.result === "PASS").length;
  const warn = checks.filter((c) => c.result === "WARN").length;
  const fail = checks.filter((c) => c.result === "FAIL").length;

  return (
    <div
      style={{
        display: "flex",
        gap: 24,
        marginBottom: 16,
        fontSize: 14,
      }}
    >
      <span>
        <span className="badge badge-pass" style={{ marginRight: 6 }}>
          PASS
        </span>
        {pass}
      </span>
      <span>
        <span className="badge badge-warn" style={{ marginRight: 6 }}>
          WARN
        </span>
        {warn}
      </span>
      <span>
        <span className="badge badge-fail" style={{ marginRight: 6 }}>
          FAIL
        </span>
        {fail}
      </span>
    </div>
  );
}

/* ---- Checks by category ---- */

function ChecksByCategory({ checks }: { checks: AuditCheck[] }) {
  const grouped = checks.reduce<Record<string, AuditCheck[]>>((acc, c) => {
    if (!acc[c.category]) acc[c.category] = [];
    acc[c.category].push(c);
    return acc;
  }, {});

  return (
    <div>
      {Object.entries(grouped).map(([category, items]) => (
        <div key={category} style={{ marginBottom: 24 }}>
          <h3
            style={{
              fontSize: 15,
              fontWeight: 600,
              color: "var(--color-text)",
              marginBottom: 8,
              textTransform: "capitalize",
            }}
          >
            {category}
          </h3>
          <div
            style={{
              background: "var(--color-surface)",
              border: "1px solid var(--color-border)",
              borderRadius: 10,
              padding: "4px 16px",
            }}
          >
            {items.map((check) => (
              <CheckRow key={check.id} check={check} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

/* ---- Audit form ---- */

interface FormState {
  strategy: string;
  startDate: string;
  endDate: string;
  initialCapital: number;
  benchmark: string;
}

const defaultForm: FormState = {
  strategy: "momentum_rotation",
  startDate: "2024-01-01",
  endDate: "2025-01-01",
  initialCapital: 1000000,
  benchmark: "510300",
};

function AuditForm({
  onSubmit,
  isLoading,
}: {
  onSubmit: (form: FormState) => void;
  isLoading: boolean;
}) {
  const [form, setForm] = useState<FormState>(defaultForm);

  const update = (key: keyof FormState, value: string | number) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(form);
  };

  return (
    <form onSubmit={handleSubmit} className="card">
      <div className="card-title">Audit Configuration</div>
      <div className="grid-col-2">
        <div className="form-group">
          <label htmlFor="aud-strategy">Strategy</label>
          <select
            id="aud-strategy"
            className="form-input"
            value={form.strategy}
            onChange={(e) => update("strategy", e.target.value)}
          >
            <option value="momentum_rotation">Momentum Rotation</option>
            <option value="min_variance">Minimum Variance</option>
            <option value="equal_weight">Equal Weight</option>
            <option value="risk_parity">Risk Parity</option>
            <option value="trend_following">Trend Following</option>
          </select>
        </div>
        <div className="form-group">
          <label htmlFor="aud-benchmark">Benchmark</label>
          <select
            id="aud-benchmark"
            className="form-input"
            value={form.benchmark}
            onChange={(e) => update("benchmark", e.target.value)}
          >
            <option value="510300">CSI 300 (510300)</option>
            <option value="510050">SSE 50 (510050)</option>
            <option value="510500">CSI 500 (510500)</option>
            <option value="159919">CSI 300 ETF (159919)</option>
          </select>
        </div>
        <div className="form-group">
          <label htmlFor="aud-start">Start Date</label>
          <input
            id="aud-start"
            type="date"
            className="form-input"
            value={form.startDate}
            onChange={(e) => update("startDate", e.target.value)}
          />
        </div>
        <div className="form-group">
          <label htmlFor="aud-end">End Date</label>
          <input
            id="aud-end"
            type="date"
            className="form-input"
            value={form.endDate}
            onChange={(e) => update("endDate", e.target.value)}
          />
        </div>
        <div className="form-group">
          <label htmlFor="aud-capital">Initial Capital (CNY)</label>
          <input
            id="aud-capital"
            type="number"
            className="form-input"
            value={form.initialCapital}
            onChange={(e) =>
              update("initialCapital", Number(e.target.value))
            }
            min={10000}
            step={10000}
          />
        </div>
      </div>
      <div style={{ marginTop: 16 }}>
        <button type="submit" className="btn btn-primary" disabled={isLoading}>
          {isLoading ? (
            <>
              <span className="state-loading-icon" />
              Running Audit...
            </>
          ) : (
            "Run Audit"
          )}
        </button>
      </div>
    </form>
  );
}

/* ---- Results ---- */

function AuditResults({
  report,
}: {
  report: NonNullable<ReturnType<typeof useAuditReport>["data"]>;
}) {
  return (
    <div style={{ marginTop: 24 }}>
      {/* Grade display */}
      <div
        className="card"
        style={{ textAlign: "center", padding: 32 }}
      >
        <p
          style={{
            fontSize: 14,
            color: "var(--color-text-muted)",
            marginBottom: 12,
            textTransform: "uppercase",
            letterSpacing: "0.05em",
          }}
        >
          Audit Grade
        </p>
        <div
          style={{
            fontSize: 48,
            fontWeight: 800,
            lineHeight: 1,
            marginBottom: 8,
            color:
              report.grade === "GREEN"
                ? "var(--color-green)"
                : report.grade === "YELLOW"
                  ? "var(--color-yellow)"
                  : "var(--color-red)",
          }}
        >
          <GradeBadge grade={report.grade} />
        </div>
        <p
          style={{
            fontSize: 17,
            color: "var(--color-text)",
            marginBottom: 4,
          }}
        >
          Score: {report.score}/{report.max_score}
        </p>
        <p
          style={{
            fontSize: 14,
            color: "var(--color-text-muted)",
            maxWidth: 600,
            margin: "0 auto",
          }}
        >
          {report.summary}
        </p>
        <p
          style={{
            marginTop: 8,
            fontSize: 12,
            color: "var(--color-text-muted)",
          }}
        >
          Run: {new Date(report.created_at).toLocaleString("en-CN")} | ID:{" "}
          {report.run_id}
        </p>
      </div>

      {/* Check summary */}
      <div className="card">
        <div className="card-title">Check Results</div>
        <CheckSummary checks={report.checks} />
        <ChecksByCategory checks={report.checks} />
      </div>
    </div>
  );
}

/* ---- Page ---- */

function Audit() {
  const [runId, setRunId] = useState<string | null>(null);
  const {
    data: report,
    error: fetchError,
    isLoading: isFetching,
  } = useAuditReport(runId);
  const {
    error: runError,
    isLoading: isRunning,
    mutate: runAudit,
  } = useMutation<{ run_id: string }>("post", "/audit/run");

  const handleRun = async (form: FormState) => {
    const res = await runAudit({
      strategy: form.strategy,
      start_date: form.startDate,
      end_date: form.endDate,
      initial_capital: form.initialCapital,
      benchmark: form.benchmark,
    });
    if (res && res.run_id) {
      setRunId(res.run_id);
    }
  };

  const displayError = runError || fetchError;
  const displayLoading = isRunning || isFetching;

  return (
    <div className="page">
      <h2>Audit</h2>

      <AuditForm onSubmit={handleRun} isLoading={isRunning} />

      {displayLoading && <AuditSkeleton />}

      {displayError && (
        <div className="state-banner state-error">
          <span>Audit failed: {displayError}</span>
        </div>
      )}

      {!displayLoading && !displayError && !report && !runId && (
        <div className="state-banner state-empty">
          Configure your audit above and click Run to see the compliance report.
        </div>
      )}

      {!displayLoading && report && <AuditResults report={report} />}
    </div>
  );
}

export default Audit;
