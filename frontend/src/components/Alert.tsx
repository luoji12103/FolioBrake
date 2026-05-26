import { ReactNode } from "react";

interface AlertProps {
  type: "info" | "success" | "warning" | "error";
  children: ReactNode;
}

export function Alert({ type, children }: AlertProps) {
  const colors = {
    info: { bg: "rgba(79, 140, 255, 0.1)", border: "var(--color-accent)", text: "var(--color-accent)" },
    success: { bg: "rgba(52, 211, 153, 0.1)", border: "var(--color-green)", text: "var(--color-green)" },
    warning: { bg: "rgba(251, 191, 36, 0.1)", border: "var(--color-yellow)", text: "var(--color-yellow)" },
    error: { bg: "rgba(248, 113, 113, 0.1)", border: "var(--color-red)", text: "var(--color-red)" },
  };
  const { bg, border, text } = colors[type];
  return (
    <div style={{ padding: "12px 16px", borderRadius: 8, background: bg, border: `1px solid ${border}`, color: text, fontSize: 14 }}>
      {children}
    </div>
  );
}
