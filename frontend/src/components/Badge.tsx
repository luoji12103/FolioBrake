interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "success" | "warning" | "error" | "info";
}

export function Badge({ children, variant = "default" }: BadgeProps) {
  const colors = {
    default: { bg: "var(--color-border)", text: "var(--color-text)" },
    success: { bg: "rgba(52, 211, 153, 0.2)", text: "var(--color-green)" },
    warning: { bg: "rgba(251, 191, 36, 0.2)", text: "var(--color-yellow)" },
    error: { bg: "rgba(248, 113, 113, 0.2)", text: "var(--color-red)" },
    info: { bg: "rgba(79, 140, 255, 0.2)", text: "var(--color-accent)" },
  };
  const { bg, text } = colors[variant];
  return (
    <span style={{ display: "inline-flex", alignItems: "center", padding: "2px 8px", borderRadius: 9999, fontSize: 12, fontWeight: 500, background: bg, color: text }}>
      {children}
    </span>
  );
}
