export function Divider({ label }: { label?: string }) {
  if (label) {
    return (
      <div style={{ display: "flex", alignItems: "center", gap: 12, margin: "16px 0" }}>
        <div style={{ flex: 1, height: 1, background: "var(--color-border)" }} />
        <span style={{ fontSize: 12, color: "var(--color-text-muted)" }}>{label}</span>
        <div style={{ flex: 1, height: 1, background: "var(--color-border)" }} />
      </div>
    );
  }
  return <div style={{ height: 1, background: "var(--color-border)", margin: "16px 0" }} />;
}
