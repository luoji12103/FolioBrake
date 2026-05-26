import { Link } from "react-router-dom";

interface BreadcrumbItem {
  label: string;
  path?: string;
}

interface BreadcrumbProps {
  items?: BreadcrumbItem[];
}

export function Breadcrumb({ items = [] }: BreadcrumbProps) {
  return (
    <nav style={{ display: "flex", gap: 8, marginBottom: 16, fontSize: 14 }}>
      {items.map((item, i) => (
        <span key={i} style={{ display: "flex", gap: 8 }}>
          {i > 0 && <span style={{ color: "var(--color-text-muted)" }}>/</span>}
          {item.path ? (
            <Link to={item.path} style={{ color: "var(--color-accent)", textDecoration: "none" }}>{item.label}</Link>
          ) : (
            <span style={{ color: "var(--color-text)" }}>{item.label}</span>
          )}
        </span>
      ))}
    </nav>
  );
}
