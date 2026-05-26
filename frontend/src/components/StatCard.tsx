interface StatCardProps {
  label: string;
  value: string | number;
  change?: number;
  icon?: string;
}

export function StatCard({ label, value, change, icon }: StatCardProps) {
  return (
    <div className="metric-card">
      <div className="metric-label">
        {icon && <span style={{ marginRight: 4 }}>{icon}</span>}
        {label}
      </div>
      <div className="metric-value">{value}</div>
      {change !== undefined && (
        <div style={{ fontSize: 12, color: change >= 0 ? "var(--color-green)" : "var(--color-red)", marginTop: 4 }}>
          {change >= 0 ? "↑" : "↓"} {Math.abs(change).toFixed(2)}%
        </div>
      )}
    </div>
  );
}
