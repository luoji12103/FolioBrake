import { ReactNode } from "react";

interface TabPanelProps {
  children: ReactNode;
  active: boolean;
}

export function TabPanel({ children, active }: TabPanelProps) {
  if (!active) return null;
  return <div style={{ padding: "16px 0" }}>{children}</div>;
}
