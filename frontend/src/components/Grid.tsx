import { ReactNode } from "react";

interface GridProps {
  children: ReactNode;
  columns?: number;
  gap?: number;
}

export function Grid({ children, columns = 3, gap = 16 }: GridProps) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: `repeat(${columns}, 1fr)`, gap }}>
      {children}
    </div>
  );
}
