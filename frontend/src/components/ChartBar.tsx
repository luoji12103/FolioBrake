interface ChartBarProps {
  x: number;
  y: number;
  width: number;
  height: number;
  color?: string;
}

export function ChartBar({ x, y, width, height, color = "var(--color-accent)" }: ChartBarProps) {
  return <rect x={x} y={y} width={width} height={height} fill={color} />;
}
