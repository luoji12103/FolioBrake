interface ChartTooltipEnhancedProps {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string; dataKey: string }>;
  label?: string;
  formatter?: (value: number, name: string) => string;
}

export function ChartTooltipEnhanced({ active, payload, label, formatter }: ChartTooltipEnhancedProps) {
  if (!active || !payload?.length) return null;
  
  return (
    <div style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: 8, padding: "12px 16px", fontSize: 13, boxShadow: "0 4px 12px rgba(0,0,0,0.3)" }}>
      {label && <div style={{ color: "var(--color-text-muted)", marginBottom: 8, fontSize: 12, fontWeight: 600 }}>{label}</div>}
      {payload.map((p, i) => (
        <div key={i} style={{ display: "flex", justifyContent: "space-between", gap: 16, marginBottom: 4 }}>
          <span style={{ color: p.color, fontWeight: 500 }}>{p.name}</span>
          <span style={{ color: "var(--color-text)", fontWeight: 600 }}>
            {formatter ? formatter(p.value, p.name) : p.value.toLocaleString()}
          </span>
        </div>
      ))}
    </div>
  );
}
