interface SkeletonProps {
  width?: number | string;
  height?: number;
  borderRadius?: string;
  count?: number;
  gap?: number;
}

export function Skeleton({ width = "100%", height = 16, borderRadius = "6px", count = 1, gap = 8 }: SkeletonProps) {
  const items = Array.from({ length: count });
  return (
    <div style={{ display: "flex", flexDirection: "column", gap }}>
      {items.map((_, i) => (
        <div key={i} style={{ width: typeof width === "number" ? `${width}px` : width, height: `${height}px`, borderRadius, background: "linear-gradient(90deg, var(--color-surface) 25%, var(--color-border) 50%, var(--color-surface) 75%)", backgroundSize: "200% 100%", animation: "shimmer 1.5s ease-in-out infinite" }} />
      ))}
    </div>
  );
}

export function SkeletonCard() {
  return (
    <div style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: "10px", padding: 20, marginBottom: 20 }}>
      <Skeleton width={120} height={14} />
      <div style={{ marginTop: 12 }}><Skeleton count={3} height={20} /></div>
    </div>
  );
}

export function SkeletonRow({ columns = 4 }: { columns?: number }) {
  return (
    <div style={{ display: "flex", gap: 14, padding: "12px 14px", borderBottom: "1px solid var(--color-border)" }}>
      {Array.from({ length: columns }).map((_, i) => (
        <div key={i} style={{ flex: 1 }}><Skeleton height={16} /></div>
      ))}
    </div>
  );
}
