interface ChartTreemapProps {
  data: Array<{ label: string; value: number; color: string }>;
  width?: number;
  height?: number;
}

export function ChartTreemap({ data, width = 400, height = 300 }: ChartTreemapProps) {
  if (!data.length) return null;
  
  const total = data.reduce((sum, d) => sum + d.value, 0);
  let currentX = 0;
  let currentY = 0;
  
  return (
    <svg width={width} height={height}>
      {data.map((d, i) => {
        const area = (d.value / total) * width * height;
        const barWidth = Math.sqrt(area);
        const barHeight = area / barWidth;
        
        const x = currentX;
        const y = currentY;
        
        currentX += barWidth;
        if (currentX >= width) {
          currentX = 0;
          currentY += barHeight;
        }
        
        return (
          <g key={i}>
            <rect x={x} y={y} width={barWidth} height={barHeight} fill={d.color} stroke="var(--color-bg)" strokeWidth={2} />
            <text x={x + barWidth / 2} y={y + barHeight / 2} textAnchor="middle" dominantBaseline="central" fontSize={10} fill="var(--color-text)">
              {d.label}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
