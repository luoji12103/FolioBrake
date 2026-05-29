import { Link, useLocation } from "react-router-dom";

const ROUTE_LABELS: Record<string, string> = {
  universe: "Universe",
  signals: "Signals",
  risk: "Risk",
  backtest: "Backtest",
  audit: "Audit",
  paper: "Paper Trading",
  settings: "Settings",
};

interface BreadcrumbItem {
  label: string;
  path?: string;
}

interface BreadcrumbProps {
  items?: BreadcrumbItem[];
}

export function Breadcrumb({ items }: BreadcrumbProps) {
  const location = useLocation();

  const resolved: BreadcrumbItem[] = items
    ?? location.pathname
      .split("/")
      .filter(Boolean)
      .map((segment, i, arr) => ({
        label: ROUTE_LABELS[segment] ?? segment.charAt(0).toUpperCase() + segment.slice(1),
        path: "/" + arr.slice(0, i + 1).join("/"),
      }));

  if (location.pathname === "/") return null;

  return (
    <nav className="breadcrumb" aria-label="Breadcrumb">
      <Link to="/" className="breadcrumb-link">Home</Link>
      {resolved.map((item, i) => (
        <span key={i} className="breadcrumb-segment">
          <span className="breadcrumb-sep">/</span>
          {item.path && i < resolved.length - 1 ? (
            <Link to={item.path} className="breadcrumb-link">{item.label}</Link>
          ) : (
            <span className="breadcrumb-current">{item.label}</span>
          )}
        </span>
      ))}
    </nav>
  );
}
