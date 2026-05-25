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
          <button key={i} onClick={() => setActive(i)} style={{ padding: "8px 16px", background: "none", border: "none", cursor: "pointer", color: i === active ? "var(--color-accent)" : "var(--color-text-muted)", borderBottom: i === active ? "2px solid var(--color-accent)" : "2px solid transparent", fontWeight: i === active ? 600 : 400, fontSize: 14 }}>
            {t.label}
          </button>
        ))}
      </div>
      {tabs[active].content}
    </div>
  );
}

export function Tooltip({ content, children }: { content: string; children: ReactNode }) {
  const [show, setShow] = useState(false);
  return (
    <div style={{ position: "relative" }} onMouseEnter={() => setShow(true)} onMouseLeave={() => setShow(false)}>
      {children}
      {show && <div style={{ position: "absolute", bottom: "100%", left: "50%", transform: "translateX(-50%)", padding: "4px 8px", background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: 6, fontSize: 12, color: "var(--color-text)", whiteSpace: "nowrap", zIndex: 100, marginBottom: 4 }}>{content}</div>}
    </div>
  );
}

export function Dropdown({ trigger, items }: { trigger: ReactNode; items: { label: string; onClick: () => void }[] }) {
  const [open, setOpen] = useState(false);
  const ref = { current: null as HTMLDivElement | null };
  if (typeof document !== "undefined") {
    import("react").then(({ useEffect, useRef }) => {
      const r = useRef<HTMLDivElement>(null);
      ref.current = r.current;
      useEffect(() => {
        const h = (e: MouseEvent) => { if (r.current && !r.current.contains(e.target as Node)) setOpen(false); };
        document.addEventListener("mousedown", h);
        return () => document.removeEventListener("mousedown", h);
      }, []);
    });
  }
  return (
    <div style={{ position: "relative" }}>
      <div onClick={() => setOpen(!open)} style={{ cursor: "pointer" }}>{trigger}</div>
      {open && (
        <div style={{ position: "absolute", top: "100%", right: 0, minWidth: 180, background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: 8, boxShadow: "0 4px 16px rgba(0,0,0,0.3)", zIndex: 100, overflow: "hidden" }}>
          {items.map((item, i) => (
            <div key={i} onClick={() => { item.onClick(); setOpen(false); }} style={{ padding: "10px 16px", cursor: "pointer", color: "var(--color-text)", fontSize: 14, borderBottom: i < items.length - 1 ? "1px solid var(--color-border)" : "none" }}>
              {item.label}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
