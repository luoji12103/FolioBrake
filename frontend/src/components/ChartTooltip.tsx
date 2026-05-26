interface ChartTooltipProps {
  label?: string;
  items: { name: string; value: string | number; color?: string }[];
}

export function ChartTooltip({ label, items }: ChartTooltipProps) {
  return (
    <div style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: 8, padding: "10px 14px", fontSize: 13 }}>
      {label && <div style={{ color: "var(--color-text-muted)", marginBottom: 4, fontSize: 12 }}>{label}</div>}
      {items.map((item, i) => (
        <div key={i} style={{ color: item.color || "var(--color-text)", fontWeight: 600 }}>
          {item.name}: {typeof item.value === "number" ? item.value.toLocaleString() : item.value}
        </div>
      ))}
    </div>
  );
}
