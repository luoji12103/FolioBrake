interface ChartAreaProps {
  data: Array<{ x: number; y: number }>;
  color?: string;
  opacity?: number;
}

export function ChartArea({ data, color = "var(--color-accent)", opacity = 0.3 }: ChartAreaProps) {
  if (!data.length) return null;
  const path = data.map((d, i) => `${i === 0 ? "M" : "L"} ${d.x} ${d.y}`).join(" ");
  return (
    <g>
      <path d={path} fill="none" stroke={color} strokeWidth={2} />
      <path d={`${path} L ${data[data.length - 1].x} ${data[data.length - 1].y} L ${data[0].x} ${data[data.length - 1].y} Z`} fill={color} opacity={opacity} />
    </g>
  );
}
