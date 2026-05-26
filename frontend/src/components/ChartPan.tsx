interface ChartPanProps {
  onPanLeft?: () => void;
  onPanRight?: () => void;
}

export function ChartPan({ onPanLeft, onPanRight }: ChartPanProps) {
  return (
    <div style={{ display: "flex", gap: 4 }}>
      <button onClick={onPanLeft} style={{ padding: "4px 8px", background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: 4, cursor: "pointer" }}>←</button>
      <button onClick={onPanRight} style={{ padding: "4px 8px", background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: 4, cursor: "pointer" }}>→</button>
    </div>
  );
}
