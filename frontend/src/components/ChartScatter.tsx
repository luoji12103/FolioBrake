interface ChartScatterProps {
  data: Array<{ x: number; y: number }>;
  color?: string;
  size?: number;
}

export function ChartScatter({ data, color = "var(--color-accent)", size = 4 }: ChartScatterProps) {
  return (
    <g>
      {data.map((d, i) => (
        <circle key={i} cx={d.x} cy={d.y} r={size} fill={color} />
      ))}
    </g>
  );
}
