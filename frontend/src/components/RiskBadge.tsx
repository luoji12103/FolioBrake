const stateColors: Record<string, string> = {
  NORMAL: "#34d399",
  CAUTION: "#fbbf24",
  DEFENSIVE: "#f97316",
  HALT: "#f87171",
};

function RiskBadge({ state }: { state: string }) {
  return (
    <span
      style={{
        padding: "4px 12px",
        borderRadius: "99px",
        fontSize: "13px",
        fontWeight: 600,
        color: "#0f1117",
        background: stateColors[state] || "#8b8fa3",
      }}
    >
      {state}
    </span>
  );
}

export default RiskBadge;
