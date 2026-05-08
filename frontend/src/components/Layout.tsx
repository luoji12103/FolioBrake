import { useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { useRiskState, useRiskAlerts } from "../api/hooks";
import RiskBadge from "./RiskBadge";
import "./Layout.css";

function Layout() {
  const { data: riskState } = useRiskState();
  const { data: alertsData } = useRiskAlerts();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const [alertsOpen, setAlertsOpen] = useState(false);

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
        <div className="header-left">
          <button className="hamburger" onClick={() => setMenuOpen(!menuOpen)} aria-label="Toggle menu">
            <span className={menuOpen ? "hamburger-line open" : "hamburger-line"} />
            <span className={menuOpen ? "hamburger-line open" : "hamburger-line"} />
            <span className={menuOpen ? "hamburger-line open" : "hamburger-line"} />
          </button>
          <h1 className="logo">FolioBrake</h1>
        </div>
        <div className="header-right">
          <RiskBadge state={riskState?.state || "NORMAL"} />
          <div style={{ position: "relative" }}>
            <button
              className="icon-btn"
              onClick={() => setAlertsOpen(!alertsOpen)}
              aria-label="Notifications"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
              </svg>
              {alertsData && alertsData.unread_count > 0 && (
                <span className="notification-badge">{alertsData.unread_count}</span>
              )}
            </button>
            {alertsOpen && (
              <div className="alerts-panel">
                <div className="alerts-header">
                  <span>Notifications</span>
                  <button className="alerts-close" onClick={() => setAlertsOpen(false)}>✕</button>
                </div>
                {alertsData?.alerts.map(alert => (
                  <div key={alert.id} className={`alert-item alert-${alert.severity.toLowerCase()}`}>
                    <div className="alert-title">{alert.title}</div>
                    <div className="alert-message">{alert.message}</div>
                    <div className="alert-time">{new Date(alert.timestamp).toLocaleString()}</div>
                  </div>
                ))}
                {(!alertsData || alertsData.alerts.length === 0) && (
                  <div className="alert-empty">No notifications</div>
                )}
              </div>
            )}
          </div>
        </div>
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
