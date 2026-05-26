interface HeatmapData {
  x: string;
  y: string;
  value: number;
}

interface HeatmapChartProps {
  data: HeatmapData[];
  width?: number;
  height?: number;
}

export function HeatmapChart({ data, width = 400, height = 300 }: HeatmapChartProps) {
  if (!data.length) return <div>No data</div>;
  
  const xLabels = [...new Set(data.map(d => d.x))];
  const yLabels = [...new Set(data.map(d => d.y))];
  const maxValue = Math.max(...data.map(d => Math.abs(d.value)));
  
  const cellWidth = (width - 80) / xLabels.length;
  const cellHeight = (height - 60) / yLabels.length;
  
  return (
    <svg width={width} height={height} style={{ background: "var(--color-bg)" }}>
      {data.map((d, i) => {
        const xIdx = xLabels.indexOf(d.x);
        const yIdx = yLabels.indexOf(d.y);
        const intensity = maxValue > 0 ? Math.abs(d.value) / maxValue : 0;
        const color = d.value >= 0 ? `rgba(52, 211, 153, ${intensity})` : `rgba(248, 113, 113, ${intensity})`;
        
        return (
          <g key={i}>
            <rect x={40 + xIdx * cellWidth} y={20 + yIdx * cellHeight} width={cellWidth - 2} height={cellHeight - 2} fill={color} />
            <text x={40 + xIdx * cellWidth + cellWidth / 2} y={20 + yIdx * cellHeight + cellHeight / 2} textAnchor="middle" dominantBaseline="middle" fontSize={10} fill="var(--color-text)">{d.value.toFixed(1)}</text>
          </g>
        );
      })}
      {xLabels.map((label, i) => <text key={label} x={40 + i * cellWidth + cellWidth / 2} y={height - 5} textAnchor="middle" fontSize={10} fill="var(--color-text-muted)">{label}</text>)}
      {yLabels.map((label, i) => <text key={label} x={35} y={20 + i * cellHeight + cellHeight / 2} textAnchor="end" dominantBaseline="middle" fontSize={10} fill="var(--color-text-muted)">{label}</text>)}
    </svg>
  );
}
