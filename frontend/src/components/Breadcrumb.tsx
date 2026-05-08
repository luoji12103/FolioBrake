import { Link, useLocation } from "react-router-dom";
import "./Breadcrumb.css";

const ROUTE_LABELS: Record<string, string> = {
  "": "Dashboard",
  universe: "Universe",
  signals: "Signals",
  risk: "Risk Overlay",
  backtest: "Backtest",
  audit: "Audit",
  paper: "Paper Portfolio",
  settings: "Settings",
};

export function Breadcrumb() {
  const location = useLocation();
  const pathnames = location.pathname.split("/").filter(Boolean);

  if (pathnames.length === 0) return null;

  return (
    <nav className="breadcrumb" aria-label="Breadcrumb">
      <Link to="/" className="breadcrumb-link">Home</Link>
      {pathnames.map((segment, index) => {
        const routeTo = `/${pathnames.slice(0, index + 1).join("/")}`;
        const isLast = index === pathnames.length - 1;
        const label = ROUTE_LABELS[segment] || segment;

        return (
          <span key={routeTo} className="breadcrumb-segment">
            <span className="breadcrumb-sep">/</span>
            {isLast ? (
              <span className="breadcrumb-current">{label}</span>
            ) : (
              <Link to={routeTo} className="breadcrumb-link">{label}</Link>
            )}
          </span>
        );
      })}
    </nav>
  );
}
