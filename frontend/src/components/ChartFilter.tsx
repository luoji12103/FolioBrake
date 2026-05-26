interface ChartFilterProps {
  filters: Array<{ label: string; value: string; active: boolean }>;
  onToggle: (value: string) => void;
}

export function ChartFilter({ filters, onToggle }: ChartFilterProps) {
  return (
    <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
      {filters.map(filter => (
        <button key={filter.value} onClick={() => onToggle(filter.value)}
          style={{ padding: "4px 10px", background: filter.active ? "var(--color-accent)" : "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: 4, cursor: "pointer", color: filter.active ? "#fff" : "var(--color-text-muted)", fontSize: 12 }}>
          {filter.label}
        </button>
      ))}
    </div>
  );
}
