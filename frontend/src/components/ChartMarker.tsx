interface ChartMarkerProps {
  x: number;
  y: number;
  type?: "circle" | "square" | "triangle";
  size?: number;
  color?: string;
}

export function ChartMarker({ x, y, type = "circle", size = 6, color = "var(--color-accent)" }: ChartMarkerProps) {
  if (type === "circle") {
    return <circle cx={x} cy={y} r={size / 2} fill={color} />;
  }
  if (type === "square") {
    return <rect x={x - size / 2} y={y - size / 2} width={size} height={size} fill={color} />;
  }
  return <polygon points={`${x},${y - size / 2} ${x - size / 2},${y + size / 2} ${x + size / 2},${y + size / 2}`} fill={color} />;
}
