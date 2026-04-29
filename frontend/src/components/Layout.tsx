import { useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { useRiskState } from "../api/hooks";
import RiskBadge from "./RiskBadge";
import "./Layout.css";

function Layout() {
  const { data: riskState } = useRiskState();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);

  const closeMenu = () => setMenuOpen(false);

  const navLinks = (
    <>
      <div className="nav-group">
        <div className="nav-group-label">Monitor</div>
        <a href="/" className={location.pathname === "/" ? "active" : ""} onClick={closeMenu}>Dashboard</a>
        <a href="/universe" className={location.pathname === "/universe" ? "active" : ""} onClick={closeMenu}>Universe</a>
      </div>
      <div className="nav-group">
        <div className="nav-group-label">Decide</div>
        <a href="/signals" className={location.pathname === "/signals" ? "active" : ""} onClick={closeMenu}>Signals</a>
        <a href="/risk" className={location.pathname === "/risk" ? "active" : ""} onClick={closeMenu}>Risk Overlay</a>
      </div>
      <div className="nav-group">
        <div className="nav-group-label">Verify</div>
        <a href="/backtest" className={location.pathname === "/backtest" ? "active" : ""} onClick={closeMenu}>Backtest</a>
        <a href="/audit" className={location.pathname === "/audit" ? "active" : ""} onClick={closeMenu}>Audit</a>
      </div>
      <div className="nav-group">
        <div className="nav-group-label">Act</div>
        <a href="/paper" className={location.pathname === "/paper" ? "active" : ""} onClick={closeMenu}>Paper Portfolio</a>
        <a href="/settings" className={location.pathname === "/settings" ? "active" : ""} onClick={closeMenu}>Settings</a>
      </div>
    </>
  );

  return (
    <div className="layout">
      <header className="header">
        <button className="hamburger" onClick={() => setMenuOpen(!menuOpen)} aria-label="Toggle menu">
          <span className={menuOpen ? "hamburger-line open" : "hamburger-line"} />
          <span className={menuOpen ? "hamburger-line open" : "hamburger-line"} />
          <span className={menuOpen ? "hamburger-line open" : "hamburger-line"} />
        </button>
        <h1 className="logo">Retail ETF Guardian</h1>
        <RiskBadge state={riskState?.state || "NORMAL"} />
      </header>
      <nav className={`sidebar ${menuOpen ? "sidebar-open" : ""}`}>
        {navLinks}
      </nav>
      {menuOpen && <div className="sidebar-overlay" onClick={closeMenu} />}
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}

export default Layout;
