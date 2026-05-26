interface GaugeChartProps {
  value: number;
  min?: number;
  max?: number;
  label?: string;
}

export function GaugeChart({ value, min = 0, max = 100, label }: GaugeChartProps) {
  const pct = ((value - min) / (max - min)) * 100;
  
  return (
    <div style={{ textAlign: "center" }}>
      <svg width={120} height={80} viewBox="0 0 120 80">
        <path d="M 10 70 A 50 50 0 0 1 110 70" fill="none" stroke="var(--color-border)" strokeWidth={8} strokeLinecap="round" />
        <path d="M 10 70 A 50 50 0 0 1 110 70" fill="none" stroke="var(--color-accent)" strokeWidth={8} strokeLinecap="round"
          strokeDasharray={`${(pct / 100) * 157} 157`} />
        <text x={60} y={65} textAnchor="middle" fontSize={18} fontWeight={600} fill="var(--color-text)">{value.toFixed(0)}</text>
      </svg>
      {label && <div style={{ fontSize: 12, color: "var(--color-text-muted)", marginTop: 4 }}>{label}</div>}
    </div>
  );
}
