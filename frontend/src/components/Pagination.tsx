interface PaginationProps {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export function Pagination({ page, totalPages, onPageChange }: PaginationProps) {
  return (
    <div style={{ display: "flex", gap: 8, justifyContent: "center", marginTop: 16 }}>
      <button className="btn-secondary" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>Previous</button>
      <span style={{ display: "flex", alignItems: "center", padding: "0 12px", color: "var(--color-text-muted)" }}>
        Page {page} of {totalPages}
      </span>
      <button className="btn-secondary" disabled={page >= totalPages} onClick={() => onPageChange(page + 1)}>Next</button>
    </div>
  );
}
