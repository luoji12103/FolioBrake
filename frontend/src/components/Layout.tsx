import { Outlet, useLocation } from "react-router-dom";
import { useRiskState } from "../api/hooks";
import RiskBadge from "./RiskBadge";
import "./Layout.css";

function Layout() {
  const { data: riskState } = useRiskState();
  const location = useLocation();

  return (
    <div className="layout">
      <header className="header">
        <h1 className="logo">Retail ETF Guardian</h1>
        <RiskBadge state={riskState?.state || "NORMAL"} />
      </header>
      <nav className="sidebar">
        <div className="nav-group">
          <div className="nav-group-label">Monitor</div>
          <a href="/" className={location.pathname === "/" ? "active" : ""}>Dashboard</a>
          <a href="/universe" className={location.pathname === "/universe" ? "active" : ""}>Universe</a>
        </div>
        <div className="nav-group">
          <div className="nav-group-label">Decide</div>
          <a href="/signals" className={location.pathname === "/signals" ? "active" : ""}>Signals</a>
          <a href="/risk" className={location.pathname === "/risk" ? "active" : ""}>Risk Overlay</a>
        </div>
        <div className="nav-group">
          <div className="nav-group-label">Verify</div>
          <a href="/backtest" className={location.pathname === "/backtest" ? "active" : ""}>Backtest</a>
          <a href="/audit" className={location.pathname === "/audit" ? "active" : ""}>Audit</a>
        </div>
        <div className="nav-group">
          <div className="nav-group-label">Act</div>
          <a href="/paper" className={location.pathname === "/paper" ? "active" : ""}>Paper Portfolio</a>
          <a href="/settings" className={location.pathname === "/settings" ? "active" : ""}>Settings</a>
        </div>
      </nav>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}

export default Layout;
