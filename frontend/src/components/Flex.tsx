import { ReactNode } from "react";

interface FlexProps {
  children: ReactNode;
  direction?: "row" | "column";
  gap?: number;
  align?: string;
  justify?: string;
}

export function Flex({ children, direction = "row", gap = 8, align, justify }: FlexProps) {
  return (
    <div style={{ display: "flex", flexDirection: direction, gap, alignItems: align, justifyContent: justify }}>
      {children}
    </div>
  );
}
