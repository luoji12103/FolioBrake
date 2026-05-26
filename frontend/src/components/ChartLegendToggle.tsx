interface ChartLegendToggleProps {
  items: Array<{ label: string; visible: boolean; color: string }>;
  onToggle: (label: string) => void;
}

export function ChartLegendToggle({ items, onToggle }: ChartLegendToggleProps) {
  return (
    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
      {items.map(item => (
        <button key={item.label} onClick={() => onToggle(item.label)}
          style={{ display: "flex", alignItems: "center", gap: 4, padding: "4px 8px", background: "none", border: "none", cursor: "pointer", opacity: item.visible ? 1 : 0.5 }}>
          <div style={{ width: 12, height: 12, borderRadius: 2, background: item.color }} />
          <span style={{ fontSize: 12, color: "var(--color-text-muted)" }}>{item.label}</span>
        </button>
      ))}
    </div>
  );
}
