import { useState } from "react";
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
      <div className="grid-col-2" style={{ marginBottom: 16, maxWidth: 500 }}>
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

      <p style={{ fontSize: 13, color: "var(--color-text-muted)", marginBottom: 12 }}>
        {filtered.length} of {instruments.length} instruments
      </p>

      {filtered.length === 0 ? (
        <div className="state-banner state-empty">No instruments match your filters.</div>
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
                  <td style={{ fontWeight: 600 }}>{inst.symbol}</td>
                  <td>{inst.name}</td>
                  <td>{inst.exchange}</td>
                  <td><span className="badge badge-ok">{inst.type}</span></td>
                  <td>{inst.category || "N/A"}</td>
                  <td>{formatDate(inst.created_at)}</td>
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
    <div style={{ marginTop: 16 }}>
      {Array.from({ length: 8 }).map((_, i) => (<SkeletonRow key={i} />))}
    </div>
  );
}

function Universe() {
  const { data: instruments, error, isLoading, refetch } = useInstruments();

  return (
    <div className="page">
      <h2>ETF Universe</h2>

      {isLoading && <UniverseSkeleton />}

      {error && <ErrorMessage message={`Failed to load instruments: ${error}`} onRetry={refetch} />}

      {!isLoading && !error && instruments && instruments.length === 0 && (
        <div className="state-banner state-empty">No instruments found in the universe.</div>
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
