import { useState, ReactNode } from "react";

interface TabsProps {
  tabs: { label: string; content: ReactNode }[];
  defaultTab?: number;
}

export function Tabs({ tabs, defaultTab = 0 }: TabsProps) {
  const [active, setActive] = useState(defaultTab);
  return (
    <div>
      <div style={{ display: "flex", gap: 4, borderBottom: "1px solid var(--color-border)", marginBottom: 16 }}>
        {tabs.map((t, i) => (
          <button key={i} onClick={() => setActive(i)}
            style={{ padding: "8px 16px", background: "none", border: "none", cursor: "pointer",
              color: i === active ? "var(--color-accent)" : "var(--color-text-muted)",
              borderBottom: i === active ? "2px solid var(--color-accent)" : "2px solid transparent",
              fontWeight: i === active ? 600 : 400, fontSize: 14 }}>
            {t.label}
          </button>
        ))}
      </div>
      {tabs[active].content}
    </div>
  );
}
