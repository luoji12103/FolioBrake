const stateColors: Record<string, string> = {
  NORMAL: "var(--color-green)",
  CAUTION: "var(--color-yellow)",
  DEFENSIVE: "var(--color-orange)",
  HALT: "var(--color-red)",
};

const stateBg: Record<string, string> = {
  NORMAL: "var(--color-green-dim)",
  CAUTION: "var(--color-yellow-dim)",
  DEFENSIVE: "rgba(251, 146, 60, 0.12)",
  HALT: "var(--color-red-dim)",
};

function RiskBadge({ state }: { state: string }) {
  const color = stateColors[state] || "var(--color-text-muted)";
  const bg = stateBg[state] || "rgba(139, 143, 163, 0.1)";

  return (
    <span
      style={{
        padding: "5px 14px",
        borderRadius: "var(--radius-full)",
        fontSize: "var(--text-xs)",
        fontWeight: 700,
        color: color,
        background: bg,
        letterSpacing: "var(--tracking-wide)",
        textTransform: "uppercase",
        border: `1px solid ${color}20`,
      }}
    >
      {state}
    </span>
  );
}

export default RiskBadge;
