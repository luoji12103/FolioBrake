interface ChartTooltipCustomProps {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: string;
  content?: React.ReactNode;
}

export function ChartTooltipCustom({ active, payload, label, content }: ChartTooltipCustomProps) {
  if (!active) return null;
  
  if (content) return <>{content}</>;
  
  return (
    <div style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: 8, padding: "10px 14px", fontSize: 13 }}>
      {label && <div style={{ color: "var(--color-text-muted)", marginBottom: 4 }}>{label}</div>}
      {payload?.map((p, i) => (
        <div key={i} style={{ color: p.color, fontWeight: 600 }}>
          {p.name}: {p.value.toLocaleString()}
        </div>
      ))}
    </div>
  );
}
