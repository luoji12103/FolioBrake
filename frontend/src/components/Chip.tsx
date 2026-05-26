interface ChipProps {
  label: string;
  onRemove?: () => void;
}

export function Chip({ label, onRemove }: ChipProps) {
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 4, padding: "4px 12px", borderRadius: 9999, background: "var(--color-surface)", border: "1px solid var(--color-border)", fontSize: 13, color: "var(--color-text)" }}>
      {label}
      {onRemove && (
        <button onClick={onRemove} style={{ background: "none", border: "none", cursor: "pointer", color: "var(--color-text-muted)", fontSize: 14, padding: 0, lineHeight: 1 }}>×</button>
      )}
    </span>
  );
}
