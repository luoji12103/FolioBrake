interface ChartAxisProps {
  labels: string[];
  position: "bottom" | "left";
}

export function ChartAxis({ labels, position }: ChartAxisProps) {
  if (position === "bottom") {
    return (
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4 }}>
        {labels.map((label, i) => <span key={i} style={{ fontSize: 10, color: "var(--color-text-muted)" }}>{label}</span>)}
      </div>
    );
  }
  return (
    <div style={{ display: "flex", flexDirection: "column", justifyContent: "space-between", marginRight: 4, height: "100%" }}>
      {labels.map((label, i) => <span key={i} style={{ fontSize: 10, color: "var(--color-text-muted)", textAlign: "right" }}>{label}</span>)}
    </div>
  );
}
