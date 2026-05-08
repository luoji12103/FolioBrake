import { useState } from "react";
import api from "../api/client";
import { ErrorMessage } from "../components/ErrorMessage";
import { useInstruments, useDataHealth, useSyncProgress, Instrument } from "../api/hooks";
import "./shared.css";

function formatDate(d: string | null): string {
  if (!d) return "N/A";
  const dt = new Date(d);
  if (isNaN(dt.getTime())) return d;
  return dt.toLocaleDateString("en-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
}

function SkeletonRow() {
  return (
    <div className="skeleton-row">
      <div className="skeleton" />
      <div className="skeleton" />
      <div className="skeleton" />
      <div className="skeleton" />
      <div className="skeleton" />
      <div className="skeleton" />
    </div>
  );
}

function UniverseTable({ instruments }: { instruments: Instrument[] }) {
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");

  const categories = Array.from(new Set(instruments.map((i) => i.category))).filter(Boolean).sort() as string[];

  const filtered = instruments.filter((i) => {
    const matchSearch =
      !search ||
      i.symbol.toLowerCase().includes(search.toLowerCase()) ||
      i.name.toLowerCase().includes(search.toLowerCase());
    const matchCat = !categoryFilter || i.category === categoryFilter;
    return matchSearch && matchCat;
  });

  return (
    <>
      <div className="grid-col-2" style={{ marginBottom: "var(--space-4)", maxWidth: 500 }}>
        <div className="form-group" style={{ marginBottom: 0 }}>
          <label htmlFor="uni-search">Search</label>
          <input
            id="uni-search"
            className="form-input"
            placeholder="Symbol or name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="form-group" style={{ marginBottom: 0 }}>
          <label htmlFor="uni-cat">Category</label>
          <select
            id="uni-cat"
            className="form-input"
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
          >
            <option value="">All Categories</option>
            {categories.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>
      </div>

      <p style={{ fontSize: "var(--text-sm)", color: "var(--color-text-dim)", marginBottom: "var(--space-3)" }}>
        {filtered.length} of {instruments.length} instruments
      </p>

      {filtered.length === 0 ? (
        <div className="state-banner state-empty">
          <div className="state-empty-icon">{"\uD83D\uDD0D"}</div>
          <div className="state-empty-title">No matches found</div>
          <div className="state-empty-desc">
            Try adjusting your search or category filter.
          </div>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Name</th>
                <th>Exchange</th>
                <th>Type</th>
                <th>Category</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((inst) => (
                <tr key={inst.symbol}>
                  <td style={{ fontWeight: 600, color: "var(--color-accent)" }}>{inst.symbol}</td>
                  <td>{inst.name}</td>
                  <td style={{ color: "var(--color-text-muted)" }}>{inst.exchange}</td>
                  <td><span className="badge badge-ok">{inst.type}</span></td>
                  <td style={{ color: "var(--color-text-muted)" }}>{inst.category || "N/A"}</td>
                  <td style={{ color: "var(--color-text-dim)", fontSize: "var(--text-xs)" }}>{formatDate(inst.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}

function UniverseSkeleton() {
  return (
    <div style={{ marginTop: "var(--space-4)" }}>
      {Array.from({ length: 8 }).map((_, i) => (<SkeletonRow key={i} />))}
    </div>
  );
}

function SyncProgressBar({ instrumentId, symbol }: { instrumentId: number; symbol: string }) {
  const progress = useSyncProgress(instrumentId, true);

  if (!progress || progress.status === "idle") return null;

  const pct = progress.progress;
  const isDone = progress.status === "done";
  const isError = progress.status === "error";

  return (
    <div style={{ marginTop: "var(--space-2)" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", marginBottom: 4 }}>
        <span style={{ fontSize: "var(--text-xs)", color: "var(--color-text-muted)", minWidth: 80 }}>
          {isError ? "Error" : isDone ? "Complete" : `Syncing ${symbol}`}
        </span>
        <span style={{ fontSize: "var(--text-xs)", color: "var(--color-text-dim)" }}>
          {progress.synced.toLocaleString()} / {progress.total.toLocaleString()}
        </span>
        <span style={{ fontSize: "var(--text-xs)", color: "var(--color-accent)", fontWeight: 600 }}>
          {pct}%
        </span>
      </div>
      <div
        style={{
          height: 4,
          borderRadius: 2,
          background: "var(--color-border)",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${pct}%`,
            borderRadius: 2,
            background: isError
              ? "var(--color-red)"
              : isDone
                ? "var(--color-green)"
                : "var(--color-accent)",
            transition: "width 0.3s ease",
          }}
        />
      </div>
      {progress.error && (
        <span style={{ fontSize: "var(--text-xs)", color: "var(--color-red)", marginTop: 2, display: "block" }}>
          {progress.error}
        </span>
      )}
    </div>
  );
}

function Universe() {
  const { data: health } = useDataHealth();
  const { data: instruments, error, isLoading, refetch } = useInstruments();
  const [newSymbol, setNewSymbol] = useState("");
  const [adding, setAdding] = useState(false);
  const [addMsg, setAddMsg] = useState<string | null>(null);
  const [syncingInstrumentId, setSyncingInstrumentId] = useState<number | null>(null);
  const [syncingSymbol, setSyncingSymbol] = useState<string>("");

  const handleAdd = async () => {
    if (!newSymbol.trim()) return;
    setAdding(true); setAddMsg(null);
    const sym = newSymbol.trim();
    try {
      const { data } = await api.post("/data/instruments", { symbol: sym });
      setSyncingInstrumentId(data.id);
      setSyncingSymbol(sym);
      setNewSymbol("");
      setAddMsg(`Added ${sym}. Syncing data...`);
      refetch();
    } catch (e: any) {
      setAddMsg(`Error: ${e?.response?.data?.detail || e.message}`);
    } finally { setAdding(false); }
  };

  return (
    <div className="page">
      <h2>ETF Universe</h2>

      <div className="card" style={{ marginBottom: "var(--space-4)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)" }}>
          <input
            className="form-input"
            style={{ maxWidth: 220 }}
            placeholder="ETF symbol (e.g. 510880)"
            value={newSymbol}
            onChange={(e) => setNewSymbol(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAdd()}
          />
          <button className="btn-primary" onClick={handleAdd} disabled={adding}>
            {adding ? "Adding..." : "Add ETF"}
          </button>
          {addMsg && (
            <span className={`toast ${addMsg.startsWith("Error") ? "toast-error" : "toast-success"}`}>
              {addMsg}
            </span>
          )}
        </div>
        {syncingInstrumentId && (
          <div style={{ marginTop: "var(--space-3)" }}>
            <SyncProgressBar instrumentId={syncingInstrumentId} symbol={syncingSymbol} />
          </div>
        )}
      </div>

      {health && (
        <div className="card" style={{ marginBottom: 16 }}>
          <div className="card-title">Data Health</div>
          <div className="metric-grid">
            <div className="metric-card">
              <div className="metric-label">Total Instruments</div>
              <div className="metric-value">{health.data_quality.total_instruments}</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Total Bars</div>
              <div className="metric-value">{health.sources[0]?.bars_count?.toLocaleString() || 0}</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Latest Data</div>
              <div className="metric-value">{health.data_quality.latest_bar_date || "N/A"}</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Stale Instruments</div>
              <div className="metric-value" style={{ color: health.data_quality.stale_instruments > 0 ? "var(--color-yellow)" : "var(--color-green)" }}>
                {health.data_quality.stale_instruments}
              </div>
            </div>
          </div>
        </div>
      )}

      {isLoading && <UniverseSkeleton />}

      {error && <ErrorMessage message={`Failed to load instruments: ${error}`} onRetry={refetch} />}

      {!isLoading && !error && instruments && instruments.length === 0 && (
        <div className="state-banner state-empty">
          <div className="state-empty-icon">{"\uD83C\uDF10"}</div>
          <div className="state-empty-title">No instruments in universe</div>
          <div className="state-empty-desc">
            Add ETF symbols above to start tracking them.
          </div>
        </div>
      )}

      {!isLoading && !error && instruments && instruments.length > 0 && (
        <div className="card">
          <UniverseTable instruments={instruments} />
        </div>
      )}
    </div>
  );
}

export default Universe;
