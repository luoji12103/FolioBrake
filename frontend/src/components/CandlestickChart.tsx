interface CandlestickData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
}

interface CandlestickChartProps {
  data: CandlestickData[];
  width?: number;
  height?: number;
}

export function CandlestickChart({ data, width = 800, height = 400 }: CandlestickChartProps) {
  if (!data.length) return <div>No data</div>;
  
  const minLow = Math.min(...data.map(d => d.low));
  const maxHigh = Math.max(...data.map(d => d.high));
  const range = maxHigh - minLow || 1;
  
  const candleWidth = Math.max(2, (width - 40) / data.length - 2);
  
  return (
    <svg width={width} height={height} style={{ background: "var(--color-bg)" }}>
      {data.map((d, i) => {
        const x = 20 + i * (candleWidth + 2);
        const isGreen = d.close >= d.open;
        const bodyTop = height - 20 - ((Math.max(d.open, d.close) - minLow) / range) * (height - 40);
        const bodyBottom = height - 20 - ((Math.min(d.open, d.close) - minLow) / range) * (height - 40);
        const wickTop = height - 20 - ((d.high - minLow) / range) * (height - 40);
        const wickBottom = height - 20 - ((d.low - minLow) / range) * (height - 40);
        
        return (
          <g key={i}>
            <line x1={x + candleWidth / 2} y1={wickTop} x2={x + candleWidth / 2} y2={wickBottom} stroke={isGreen ? "var(--color-green)" : "var(--color-red)"} strokeWidth={1} />
            <rect x={x} y={bodyTop} width={candleWidth} height={Math.max(1, bodyBottom - bodyTop)} fill={isGreen ? "var(--color-green)" : "var(--color-red)"} />
          </g>
        );
      })}
    </svg>
  );
}
