interface ChartAnnotationEnhancedProps {
  x: number;
  y: number;
  label: string;
  color?: string;
  size?: number;
}

export function ChartAnnotationEnhanced({ x, y, label, color = "var(--color-accent)", size = 12 }: ChartAnnotationEnhancedProps) {
  return (
    <g>
      <circle cx={x} cy={y} r={size / 2} fill={color} opacity={0.3} />
      <circle cx={x} cy={y} r={size / 4} fill={color} />
      <text x={x} y={y - size} textAnchor="middle" fontSize={10} fill={color}>{label}</text>
    </g>
  );
}
