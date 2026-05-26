interface ChartWaterfallProps {
  data: Array<{ label: string; value: number; color?: string }>;
  width?: number;
  height?: number;
}

export function ChartWaterfall({ data, width = 400, height = 300 }: ChartWaterfallProps) {
  if (!data.length) return null;
  
  const maxValue = Math.max(...data.map(d => Math.abs(d.value)));
  const barWidth = width / data.length - 4;
  let cumulative = 0;
  
  return (
    <svg width={width} height={height}>
      {data.map((d, i) => {
        const barHeight = (Math.abs(d.value) / maxValue) * height * 0.8;
        const y = d.value >= 0 ? height - cumulative - barHeight : height - cumulative;
        const x = i * (barWidth + 4);
        
        cumulative += d.value;
        
        return (
          <g key={i}>
            <rect x={x} y={y} width={barWidth} height={barHeight} fill={d.color || (d.value >= 0 ? "var(--color-green)" : "var(--color-red)")} rx={2} />
            <text x={x + barWidth / 2} y={height - 5} textAnchor="middle" fontSize={10} fill="var(--color-text-muted)">{d.label}</text>
          </g>
        );
      })}
    </svg>
  );
}
