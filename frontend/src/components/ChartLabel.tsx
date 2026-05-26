interface ChartLabelProps {
  x: number;
  y: number;
  text: string;
  color?: string;
  fontSize?: number;
  anchor?: "start" | "middle" | "end";
}

export function ChartLabel({ x, y, text, color = "var(--color-text)", fontSize = 12, anchor = "middle" }: ChartLabelProps) {
  return (
    <text x={x} y={y} textAnchor={anchor} fontSize={fontSize} fill={color}>
      {text}
    </text>
  );
}
