import { ReactNode } from "react";

interface ChartWrapperProps {
  title: string;
  children: ReactNode;
  height?: number;
}

export function ChartWrapper({ title, children, height = 400 }: ChartWrapperProps) {
  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div className="card-title">{title}</div>
      <div style={{ height }}>{children}</div>
    </div>
  );
}
