interface ChartCrosshairProps {
  x?: number;
  y?: number;
  visible?: boolean;
}

export function ChartCrosshair({ visible }: ChartCrosshairProps) {
  if (!visible) return null;
  return null;
}
