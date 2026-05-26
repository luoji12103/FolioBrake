interface ChartZoomProps {
  onZoomIn?: () => void;
  onZoomOut?: () => void;
  onReset?: () => void;
}

export function ChartZoom({ onZoomIn, onZoomOut, onReset }: ChartZoomProps) {
  return (
    <div style={{ display: "flex", gap: 4 }}>
      <button onClick={onZoomIn} style={{ padding: "4px 8px", background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: 4, cursor: "pointer" }}>+</button>
      <button onClick={onZoomOut} style={{ padding: "4px 8px", background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: 4, cursor: "pointer" }}>-</button>
      <button onClick={onReset} style={{ padding: "4px 8px", background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: 4, cursor: "pointer" }}>Reset</button>
    </div>
  );
}
