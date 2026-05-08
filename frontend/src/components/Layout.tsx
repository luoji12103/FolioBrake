import { useState, useEffect, useCallback, useMemo } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { useRiskState, useRiskAlerts, type AlertCategory } from "../api/hooks";
import { useKeyboardShortcuts } from "../hooks/useKeyboardShortcuts";
import { useI18n } from "../i18n";
import { Kbd } from "./Kbd";
import { CommandPalette } from "./CommandPalette";
import { ShortcutHelper } from "./ShortcutHelper";
import { Breadcrumb } from "./Breadcrumb";
import { LoadingBar } from "./LoadingBar";
import RiskBadge from "./RiskBadge";
import "./Layout.css";

function ThemeToggle({ theme, onToggle }: { theme: string; onToggle: () => void }) {
  return (
    <button
      className="icon-btn"
      onClick={onToggle}
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

function LocaleToggle() {
  const { locale, setLocale } = useI18n();
  return (
    <button
      className="icon-btn locale-toggle"
      onClick={() => setLocale(locale === "zh" ? "en" : "zh")}
      aria-label={`Switch to ${locale === "zh" ? "English" : "中文"}`}
      title={locale === "zh" ? "English" : "中文"}
      style={{ fontSize: 12, fontWeight: 700, width: "auto", padding: "0 8px" }}
    >
      {locale === "zh" ? "EN" : "中"}
    </button>
  );
}

function Layout() {
  const { data: riskState } = useRiskState();
  const { data: alertsData } = useRiskAlerts();
  const location = useLocation();
  const { t } = useI18n();
  const [theme, setTheme] = useState(() => localStorage.getItem("theme") || "dark");
  const [menuOpen, setMenuOpen] = useState(false);
  const [alertsOpen, setAlertsOpen] = useState(false);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [helperOpen, setHelperOpen] = useState(false);
  const [alertFilter, setAlertFilter] = useState<AlertCategory | "all">("all");

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  const closeMenu = () => setMenuOpen(false);

  const toggleTheme = useCallback(() => {
    setTheme(t => (t === "dark" ? "light" : "dark"));
  }, []);

  const refreshPage = useCallback(() => {
    window.dispatchEvent(new Event("refresh-data"));
  }, []);

  useKeyboardShortcuts({
    "Ctrl+K": () => setPaletteOpen((o) => !o),
    "Shift+/": () => setHelperOpen((o) => !o),
    "Ctrl+Shift+L": toggleTheme,
    "Ctrl+Shift+R": refreshPage,
    "Escape": () => {
      setPaletteOpen(false);
      setHelperOpen(false);
      setAlertsOpen(false);
      setMenuOpen(false);
    },
  });

  const navLinks = (
    <>
      <div className="nav-group">
        <div className="nav-group-label">{t("nav.monitor")}</div>
        <a href="/" className={location.pathname === "/" ? "active" : ""} onClick={closeMenu}>{t("nav.dashboard")}</a>
        <a href="/universe" className={location.pathname === "/universe" ? "active" : ""} onClick={closeMenu}>{t("nav.universe")}</a>
      </div>
      <div className="nav-group">
        <div className="nav-group-label">{t("nav.decide")}</div>
        <a href="/signals" className={location.pathname === "/signals" ? "active" : ""} onClick={closeMenu}>{t("nav.signals")}</a>
        <a href="/risk" className={location.pathname === "/risk" ? "active" : ""} onClick={closeMenu}>{t("nav.riskOverlay")}</a>
      </div>
      <div className="nav-group">
        <div className="nav-group-label">{t("nav.verify")}</div>
        <a href="/backtest" className={location.pathname === "/backtest" ? "active" : ""} onClick={closeMenu}>{t("nav.backtest")}</a>
        <a href="/audit" className={location.pathname === "/audit" ? "active" : ""} onClick={closeMenu}>{t("nav.audit")}</a>
      </div>
      <div className="nav-group">
        <div className="nav-group-label">{t("nav.act")}</div>
        <a href="/paper" className={location.pathname === "/paper" ? "active" : ""} onClick={closeMenu}>{t("nav.paperPortfolio")}</a>
        <a href="/settings" className={location.pathname === "/settings" ? "active" : ""} onClick={closeMenu}>{t("nav.settings")}</a>
      </div>
    </>
  );

  const filteredAlerts = useMemo(() => {
    if (!alertsData) return [];
    if (alertFilter === "all") return alertsData.alerts;
    return alertsData.alerts.filter((a) => a.category === alertFilter);
  }, [alertsData, alertFilter]);

  const categoryFilters: { key: AlertCategory | "all"; label: string }[] = [
    { key: "all", label: t("common.all") },
    { key: "risk", label: t("alerts.risk") },
    { key: "signal", label: t("alerts.signal") },
    { key: "trade", label: t("alerts.trade") },
    { key: "system", label: t("alerts.system") },
  ];

  return (
    <div className="layout">
      <LoadingBar />
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
          <button
            className="search-trigger"
            onClick={() => setPaletteOpen(true)}
            aria-label="Search commands"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <span className="search-trigger-label">Search...</span>
            <Kbd combo="Ctrl+K" />
          </button>
          <ThemeToggle theme={theme} onToggle={toggleTheme} />
          <LocaleToggle />
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
                  <span>{t("alerts.title")}</span>
                  <button className="alerts-close" onClick={() => setAlertsOpen(false)}>✕</button>
                </div>
                <div className="alerts-filters">
                  {categoryFilters.map((f) => (
                    <button
                      key={f.key}
                      className={`alerts-filter-btn${alertFilter === f.key ? " active" : ""}`}
                      onClick={() => setAlertFilter(f.key)}
                    >
                      {f.label}
                    </button>
                  ))}
                </div>
                {filteredAlerts.map((alert) => (
                  <div key={alert.id} className={`alert-item alert-${alert.severity.toLowerCase()}`}>
                    <div className="alert-title-row">
                      <span className="alert-title">{alert.title}</span>
                      <span className={`alert-priority alert-priority-${alert.priority}`}>{alert.priority}</span>
                    </div>
                    <div className="alert-message">{alert.message}</div>
                    <div className="alert-meta">
                      <span className={`alert-category-tag alert-category-${alert.category}`}>{alert.category}</span>
                      <span className="alert-time">{new Date(alert.timestamp).toLocaleString()}</span>
                    </div>
                  </div>
                ))}
                {filteredAlerts.length === 0 && (
                  <div className="alert-empty">{t("alerts.noAlerts")}</div>
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
        <Breadcrumb />
        <Outlet />
      </main>
      <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} onToggleTheme={toggleTheme} />
      <ShortcutHelper open={helperOpen} onClose={() => setHelperOpen(false)} />
    </div>
  );
}

export default Layout;
