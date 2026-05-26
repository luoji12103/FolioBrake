import { ReactNode } from "react";

interface ResponsiveLayoutProps {
  children: ReactNode;
  sidebar?: ReactNode;
}

export function ResponsiveLayout({ children, sidebar }: ResponsiveLayoutProps) {
  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      {sidebar && <aside style={{ width: 240, borderRight: "1px solid var(--color-border)", padding: 16 }}>{sidebar}</aside>}
      <main style={{ flex: 1, padding: 24 }}>{children}</main>
    </div>
  );
}
