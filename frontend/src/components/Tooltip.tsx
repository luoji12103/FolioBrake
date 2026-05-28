import { useState, ReactNode } from "react";

export function Tooltip({ content, children }: { content: string; children: ReactNode }) {
  const [show, setShow] = useState(false);
  return (
    <div style={{ position: "relative" }} onMouseEnter={() => setShow(true)} onMouseLeave={() => setShow(false)}>
      {children}
      {show && (
        <div style={{
          position: "absolute", bottom: "100%", left: "50%", transform: "translateX(-50%)",
          padding: "4px 8px", background: "var(--color-surface)", border: "1px solid var(--color-border)",
          borderRadius: 6, fontSize: 12, color: "var(--color-text)", whiteSpace: "nowrap", zIndex: 100, marginBottom: 4
        }}>
          {content}
        </div>
      )}
    </div>
  );
}
