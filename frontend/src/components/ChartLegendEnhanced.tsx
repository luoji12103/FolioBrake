interface ChartLegendEnhancedProps {
  payload?: Array<{ value: string; color: string; type?: string }>;
  onToggle?: (value: string) => void;
}

export function ChartLegendEnhanced({ payload, onToggle }: ChartLegendEnhancedProps) {
  if (!payload?.length) return null;
  
  return (
    <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginTop: 12, justifyContent: "center" }}>
      {payload.map((entry, i) => (
        <button key={i} onClick={() => onToggle?.(entry.value)}
          style={{ display: "flex", alignItems: "center", gap: 6, padding: "4px 10px", background: "none", border: "1px solid var(--color-border)", borderRadius: 6, cursor: "pointer", fontSize: 12 }}>
          <div style={{ width: 10, height: 10, borderRadius: 2, background: entry.color }} />
          <span style={{ color: "var(--color-text-muted)" }}>{entry.value}</span>
        </button>
      ))}
    </div>
  );
}
