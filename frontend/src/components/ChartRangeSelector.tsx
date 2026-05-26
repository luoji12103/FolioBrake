interface ChartRangeSelectorProps {
  ranges: string[];
  selected: string;
  onChange: (range: string) => void;
}

export function ChartRangeSelector({ ranges, selected, onChange }: ChartRangeSelectorProps) {
  return (
    <div style={{ display: "flex", gap: 4 }}>
      {ranges.map(range => (
        <button key={range} onClick={() => onChange(range)}
          style={{ padding: "4px 8px", background: range === selected ? "var(--color-accent)" : "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: 4, cursor: "pointer", color: range === selected ? "#fff" : "var(--color-text)", fontSize: 12 }}>
          {range}
        </button>
      ))}
    </div>
  );
}
