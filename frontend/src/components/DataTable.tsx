import { useState, useMemo, useCallback } from "react";
import "./DataTable.css";

export interface ColumnDef<T> {
  /** Key of the data object this column displays */
  key: keyof T & string;
  /** Header label */
  label: string;
  /** Whether this column is sortable (default: false) */
  sortable?: boolean;
  /** Custom cell renderer — return JSX for rich content */
  render?: (value: T[keyof T], row: T) => React.ReactNode;
  /** Optional alignment */
  align?: "left" | "center" | "right";
}

export interface DataTableProps<T extends Record<string, unknown>> {
  /** Row data */
  data: T[];
  /** Column definitions */
  columns: ColumnDef<T>[];
  /** Rows per page (default 20) */
  pageSize?: number;
  /** Placeholder for the filter input */
  filterPlaceholder?: string;
  /** Show the filter input (default true) */
  showFilter?: boolean;
  /** Show pagination (default true) */
  showPagination?: boolean;
  /** Row key accessor — defaults to row index */
  rowKey?: (row: T, index: number) => string | number;
  /** Callback when a row is clicked */
  onRowClick?: (row: T) => void;
  /** Custom empty-state message */
  emptyMessage?: string;
}

type SortDir = "asc" | "desc";

export function DataTable<T extends Record<string, unknown>>({
  data,
  columns,
  pageSize = 20,
  filterPlaceholder = "Filter rows\u2026",
  showFilter = true,
  showPagination = true,
  rowKey,
  onRowClick,
  emptyMessage = "No data to display",
}: DataTableProps<T>) {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<SortDir>("asc");
  const [filter, setFilter] = useState("");
  const [page, setPage] = useState(0);

  // --- Filtering ---
  const filtered = useMemo(() => {
    if (!filter.trim()) return data;
    const lower = filter.toLowerCase();
    return data.filter((row) =>
      Object.values(row).some((v) => String(v).toLowerCase().includes(lower))
    );
  }, [data, filter]);

  // --- Sorting ---
  const sorted = useMemo(() => {
    if (!sortKey) return filtered;
    return [...filtered].sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];
      if (aVal == null && bVal == null) return 0;
      if (aVal == null) return 1;
      if (bVal == null) return -1;

      let cmp: number;
      if (typeof aVal === "number" && typeof bVal === "number") {
        cmp = aVal - bVal;
      } else {
        cmp = String(aVal).localeCompare(String(bVal));
      }
      return sortDir === "asc" ? cmp : -cmp;
    });
  }, [filtered, sortKey, sortDir]);

  // --- Pagination ---
  const totalPages = Math.max(1, Math.ceil(sorted.length / pageSize));
  const safePage = Math.min(page, totalPages - 1);
  const paged = showPagination
    ? sorted.slice(safePage * pageSize, (safePage + 1) * pageSize)
    : sorted;

  // Reset page when filter changes
  const handleFilterChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setFilter(e.target.value);
      setPage(0);
    },
    []
  );

  const handleSort = useCallback(
    (colKey: string) => {
      setPage(0);
      if (sortKey === colKey) {
        setSortDir((d) => (d === "asc" ? "desc" : "asc"));
      } else {
        setSortKey(colKey);
        setSortDir("asc");
      }
    },
    [sortKey]
  );

  const getRowKey = rowKey ?? ((_: T, i: number) => i);

  // --- Render ---
  return (
    <div className="data-table">
      {showFilter && (
        <div className="data-table-toolbar">
          <div className="data-table-filter">
            <svg
              className="data-table-filter-icon"
              viewBox="0 0 16 16"
              fill="none"
              aria-hidden="true"
            >
              <circle cx="6.5" cy="6.5" r="5" stroke="currentColor" strokeWidth="1.5" />
              <path d="M10.5 10.5L14.5 14.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
            <input
              type="text"
              className="data-table-filter-input"
              placeholder={filterPlaceholder}
              value={filter}
              onChange={handleFilterChange}
            />
            {filter && (
              <button
                className="data-table-filter-clear"
                onClick={() => { setFilter(""); setPage(0); }}
                aria-label="Clear filter"
              >
                &times;
              </button>
            )}
          </div>
          {filter && (
            <span className="data-table-count">
              {sorted.length} of {data.length} rows
            </span>
          )}
        </div>
      )}

      <div className="data-table-scroll">
        <table className="data-table-table">
          <thead>
            <tr>
              {columns.map((col) => {
                const isSorted = sortKey === col.key;
                return (
                  <th
                    key={col.key}
                    className={
                      col.sortable ? "data-table-th-sortable" : undefined
                    }
                    style={{ textAlign: col.align ?? "left" }}
                    onClick={col.sortable ? () => handleSort(col.key) : undefined}
                  >
                    <span className="data-table-th-content">
                      {col.label}
                      {col.sortable && (
                        <span className="data-table-sort-indicator">
                          {isSorted ? (
                            sortDir === "asc" ? (
                              <svg viewBox="0 0 10 6" fill="currentColor" aria-hidden="true">
                                <path d="M5 0L10 6H0L5 0Z" />
                              </svg>
                            ) : (
                              <svg viewBox="0 0 10 6" fill="currentColor" aria-hidden="true">
                                <path d="M5 6L0 0H10L5 6Z" />
                              </svg>
                            )
                          ) : (
                            <svg viewBox="0 0 10 6" fill="currentColor" aria-hidden="true" className="data-table-sort-idle">
                              <path d="M5 0L10 6H0L5 0Z" />
                            </svg>
                          )}
                        </span>
                      )}
                    </span>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {paged.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="data-table-empty">
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              paged.map((row, i) => (
                <tr
                  key={getRowKey(row, safePage * pageSize + i)}
                  className={onRowClick ? "data-table-row-clickable" : undefined}
                  onClick={onRowClick ? () => onRowClick(row) : undefined}
                >
                  {columns.map((col) => (
                    <td
                      key={col.key}
                      style={{ textAlign: col.align ?? "left" }}
                    >
                      {col.render
                        ? col.render(row[col.key], row)
                        : String(row[col.key] ?? "")}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {showPagination && sorted.length > pageSize && (
        <div className="data-table-pagination">
          <button
            className="data-table-page-btn"
            disabled={safePage === 0}
            onClick={() => setPage(0)}
            aria-label="First page"
          >
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
              <path d="M10 12L6 8L10 4" />
              <path d="M6 12L2 8L6 4" />
            </svg>
          </button>
          <button
            className="data-table-page-btn"
            disabled={safePage === 0}
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            aria-label="Previous page"
          >
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
              <path d="M10 12L6 8L10 4" />
            </svg>
          </button>
          <span className="data-table-page-info">
            {safePage + 1} / {totalPages}
          </span>
          <button
            className="data-table-page-btn"
            disabled={safePage >= totalPages - 1}
            onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            aria-label="Next page"
          >
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
              <path d="M6 4L10 8L6 12" />
            </svg>
          </button>
          <button
            className="data-table-page-btn"
            disabled={safePage >= totalPages - 1}
            onClick={() => setPage(totalPages - 1)}
            aria-label="Last page"
          >
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
              <path d="M6 4L10 8L6 12" />
              <path d="M10 4L14 8L10 12" />
            </svg>
          </button>
        </div>
      )}
    </div>
  );
}
