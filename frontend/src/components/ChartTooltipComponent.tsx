interface ChartTooltipComponentProps {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: string;
}

export function ChartTooltipComponent({ active, payload, label }: ChartTooltipComponentProps) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: 8, padding: "10px 14px", fontSize: 13 }}>
      {label && <div style={{ color: "var(--color-text-muted)", marginBottom: 4, fontSize: 12 }}>{label}</div>}
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color, fontWeight: 600 }}>
          {p.name}: {typeof p.value === "number" ? p.value.toLocaleString() : p.value}
        </div>
      ))}
    </div>
  );
}
