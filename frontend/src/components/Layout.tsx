import { useState, useEffect } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { useRiskState, useRiskAlerts } from "../api/hooks";
import RiskBadge from "./RiskBadge";
import "./Layout.css";

function ThemeToggle() {
  const [theme, setTheme] = useState(() => localStorage.getItem("theme") || "dark");

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  return (
    <button
      className="icon-btn"
      onClick={() => setTheme(t => (t === "dark" ? "light" : "dark"))}
      aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
      title={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
    >
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        {theme === "dark" ? (
          <>
            <circle cx="12" cy="12" r="5" />
            <line x1="12" y1="1" x2="12" y2="3" />
            <line x1="12" y1="21" x2="12" y2="23" />
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
            <line x1="1" y1="12" x2="3" y2="12" />
            <line x1="21" y1="12" x2="23" y2="12" />
            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
            <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
          </>
        ) : (
          <>
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
          </>
        )}
      </svg>
    </button>
  );
}

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
          <ThemeToggle />
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
