import { useState } from "react";
import api from "../api/client";
import { ErrorMessage } from "../components/ErrorMessage";
import { useInstruments, Instrument } from "../api/hooks";
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

function Universe() {
  const { data: instruments, error, isLoading, refetch } = useInstruments();
  const [newSymbol, setNewSymbol] = useState("");
  const [adding, setAdding] = useState(false);
  const [addMsg, setAddMsg] = useState<string | null>(null);

  const handleAdd = async () => {
    if (!newSymbol.trim()) return;
    setAdding(true); setAddMsg(null);
    try {
      await api.post("/data/instruments", { symbol: newSymbol.trim() });
      setNewSymbol("");
      setAddMsg(`Added ${newSymbol.trim()}. Syncing data...`);
      refetch();
    } catch (e: any) {
      setAddMsg(`Error: ${e?.response?.data?.detail || e.message}`);
    } finally { setAdding(false); }
  };

  return (
    <div className="page">
      <h2>ETF Universe</h2>

      <div className="card" style={{ marginBottom: "var(--space-4)", display: "flex", alignItems: "center", gap: "var(--space-3)" }}>
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
