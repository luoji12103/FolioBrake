interface ChartLineProps {
  data: Array<{ x: number; y: number }>;
  color?: string;
  strokeWidth?: number;
  dashed?: boolean;
}

export function ChartLine({ data, color = "var(--color-accent)", strokeWidth = 2, dashed }: ChartLineProps) {
  if (!data.length) return null;
  const path = data.map((d, i) => `${i === 0 ? "M" : "L"} ${d.x} ${d.y}`).join(" ");
  return <path d={path} fill="none" stroke={color} strokeWidth={strokeWidth} strokeDasharray={dashed ? "5 5" : undefined} />;
}
