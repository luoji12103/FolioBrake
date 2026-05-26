interface ChartAxisComponentProps {
  x?: number;
  y?: number;
  payload?: { value: string };
  orientation?: "top" | "bottom" | "left" | "right";
}

export function ChartAxisComponent({ x, y, payload }: ChartAxisComponentProps) {
  if (!payload) return null;
  return (
    <text x={x} y={y} textAnchor="middle" dominantBaseline="central" style={{ fontSize: 11, fill: "var(--color-text-muted)" }}>
      {payload.value}
    </text>
  );
}
