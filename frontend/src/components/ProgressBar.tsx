interface ProgressBarProps {
  value: number;
  max?: number;
  color?: string;
  showLabel?: boolean;
}

export function ProgressBar({ value, max = 100, color = "var(--color-accent)", showLabel = true }: ProgressBarProps) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  return (
    <div style={{ width: "100%", height: 8, background: "var(--color-border)", borderRadius: 4, overflow: "hidden" }}>
      <div style={{ width: `${pct}%`, height: "100%", background: color, borderRadius: 4, transition: "width 0.3s ease" }} />
      {showLabel && <span style={{ fontSize: 12, color: "var(--color-text-muted)", marginTop: 4, display: "block" }}>{pct.toFixed(0)}%</span>}
    </div>
  );
}
