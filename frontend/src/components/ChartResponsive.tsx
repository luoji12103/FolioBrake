import { useRef, useState, useEffect } from "react";

interface ChartResponsiveProps {
  children: (width: number, height: number) => React.ReactNode;
  aspectRatio?: number;
}

export function ChartResponsive({ children, aspectRatio = 16 / 9 }: ChartResponsiveProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ width: 800, height: 450 });
  
  useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const width = entry.contentRect.width;
        setSize({ width, height: width / aspectRatio });
      }
    });
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, [aspectRatio]);
  
  return (
    <div ref={containerRef} style={{ width: "100%" }}>
      {children(size.width, size.height)}
    </div>
  );
}
