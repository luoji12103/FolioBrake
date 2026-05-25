import { useState, useEffect, useRef, ReactNode } from "react";

interface DropdownProps {
  trigger: ReactNode;
  items: { label: string; onClick: () => void }[];
}

export function Dropdown({ trigger, items }: DropdownProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  return (
    <div ref={ref} style={{ position: "relative" }}>
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
