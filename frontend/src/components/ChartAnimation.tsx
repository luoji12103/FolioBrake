import { useEffect, useState } from "react";

interface ChartAnimationProps {
  children: React.ReactNode;
  duration?: number;
}

export function ChartAnimation({ children, duration = 500 }: ChartAnimationProps) {
  const [opacity, setOpacity] = useState(0);
  
  useEffect(() => {
    const timer = setTimeout(() => setOpacity(1), 50);
    return () => clearTimeout(timer);
  }, []);
  
  return (
    <div style={{ opacity, transition: `opacity ${duration}ms ease-in-out` }}>
      {children}
    </div>
  );
}
