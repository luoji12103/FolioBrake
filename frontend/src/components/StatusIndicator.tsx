interface StatusIndicatorProps {
  status: "online" | "offline" | "warning" | "error";
  label?: string;
}

export function StatusIndicator({ status, label }: StatusIndicatorProps) {
  const colors = {
    online: "var(--color-green)",
    offline: "var(--color-text-muted)",
    warning: "var(--color-yellow)",
    error: "var(--color-red)",
  };
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <div style={{ width: 8, height: 8, borderRadius: "50%", background: colors[status] }} />
      {label && <span style={{ fontSize: 13, color: "var(--color-text-muted)" }}>{label}</span>}
    </div>
  );
}
