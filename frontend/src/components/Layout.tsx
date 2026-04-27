import { Outlet } from "react-router-dom";
import RiskBadge from "./RiskBadge";
import "./Layout.css";

function Layout() {
  return (
    <div className="layout">
      <header className="header">
        <h1 className="logo">Retail ETF Guardian</h1>
        <RiskBadge state="NORMAL" />
      </header>
      <nav className="sidebar">
        <a href="/">Dashboard</a>
        <a href="/universe">Universe</a>
        <a href="/signals">Signals</a>
        <a href="/risk">Risk Overlay</a>
        <a href="/backtest">Backtest</a>
        <a href="/audit">Audit</a>
        <a href="/paper">Paper Portfolio</a>
        <a href="/settings">Settings</a>
      </nav>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}

export default Layout;
