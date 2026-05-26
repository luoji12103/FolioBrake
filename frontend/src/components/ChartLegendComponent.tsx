interface ChartLegendComponentProps {
  payload?: Array<{ value: string; color: string }>;
}

export function ChartLegendComponent({ payload }: ChartLegendComponentProps) {
  if (!payload?.length) return null;
  return (
    <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginTop: 8 }}>
      {payload.map((entry, i) => (
        <div key={i} style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <div style={{ width: 12, height: 12, borderRadius: 2, background: entry.color }} />
          <span style={{ fontSize: 12, color: "var(--color-text-muted)" }}>{entry.value}</span>
        </div>
      ))}
    </div>
  );
}
