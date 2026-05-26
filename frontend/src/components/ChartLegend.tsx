interface ChartLegendProps {
  items: { label: string; color: string }[];
}

export function ChartLegend({ items }: ChartLegendProps) {
  return (
    <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginTop: 8 }}>
      {items.map((item, i) => (
        <div key={i} style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <div style={{ width: 12, height: 12, borderRadius: 2, background: item.color }} />
          <span style={{ fontSize: 12, color: "var(--color-text-muted)" }}>{item.label}</span>
        </div>
      ))}
    </div>
  );
}
