interface ChartDataLabelProps {
  x: number;
  y: number;
  value: string | number;
  color?: string;
}

export function ChartDataLabel({ x, y, value, color = "var(--color-text)" }: ChartDataLabelProps) {
  return (
    <text x={x} y={y} textAnchor="middle" dominantBaseline="central" style={{ fontSize: 10, fill: color }}>
      {typeof value === "number" ? value.toFixed(2) : value}
    </text>
  );
}
