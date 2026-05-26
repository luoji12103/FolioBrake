interface ChartBrushProps {
  data: Array<{ date: string }>;
  startIndex?: number;
  endIndex?: number;
  onChange?: (startIndex: number, endIndex: number) => void;
}

export function ChartBrush(_props: ChartBrushProps) {
  return null;
}
