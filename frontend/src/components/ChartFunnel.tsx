interface ChartFunnelProps {
  data: Array<{ label: string; value: number; color: string }>;
  width?: number;
  height?: number;
}

export function ChartFunnel({ data, width = 400, height = 300 }: ChartFunnelProps) {
  if (!data.length) return null;
  
  const maxValue = Math.max(...data.map(d => d.value));
  const barHeight = height / data.length;
  
  return (
    <svg width={width} height={height}>
      {data.map((d, i) => {
        const barWidth = (d.value / maxValue) * width * 0.8;
        const x = (width - barWidth) / 2;
        const y = i * barHeight;
        
        return (
          <g key={i}>
            <rect x={x} y={y} width={barWidth} height={barHeight - 2} fill={d.color} rx={4} />
            <text x={width / 2} y={y + barHeight / 2} textAnchor="middle" dominantBaseline="central" fontSize={12} fill="var(--color-text)">
              {d.label}: {d.value}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
