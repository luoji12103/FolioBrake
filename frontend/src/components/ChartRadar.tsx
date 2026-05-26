interface ChartRadarProps {
  data: Array<{ label: string; value: number }>;
  size?: number;
}

export function ChartRadar({ data, size = 200 }: ChartRadarProps) {
  if (!data.length) return null;
  
  const center = size / 2;
  const radius = size * 0.4;
  const angleStep = (2 * Math.PI) / data.length;
  
  const points = data.map((d, i) => {
    const angle = i * angleStep - Math.PI / 2;
    const r = (d.value / 100) * radius;
    return {
      x: center + r * Math.cos(angle),
      y: center + r * Math.sin(angle),
    };
  });
  
  const path = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ") + " Z";
  
  return (
    <svg width={size} height={size}>
      <path d={path} fill="var(--color-accent)" fillOpacity={0.2} stroke="var(--color-accent)" strokeWidth={2} />
      {points.map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r={4} fill="var(--color-accent)" />
      ))}
    </svg>
  );
}
