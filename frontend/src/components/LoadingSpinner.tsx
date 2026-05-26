interface LoadingSpinnerProps {
  size?: number;
  color?: string;
}

export function LoadingSpinner({ size = 24, color = "var(--color-accent)" }: LoadingSpinnerProps) {
  return (
    <div style={{ display: "inline-block", width: size, height: size, border: `2px solid var(--color-border)`, borderTopColor: color, borderRadius: "50%", animation: "spin 0.8s linear infinite" }} />
  );
}
