interface ChartSelectionProps {
  options: Array<{ label: string; value: string }>;
  selected: string;
  onChange: (value: string) => void;
}

export function ChartSelection({ options, selected, onChange }: ChartSelectionProps) {
  return (
    <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
      {options.map(opt => (
        <button key={opt.value} onClick={() => onChange(opt.value)}
          style={{ padding: "6px 12px", background: opt.value === selected ? "var(--color-accent)" : "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: 6, cursor: "pointer", color: opt.value === selected ? "#fff" : "var(--color-text)", fontSize: 13, fontWeight: opt.value === selected ? 600 : 400 }}>
          {opt.label}
        </button>
      ))}
    </div>
  );
}
