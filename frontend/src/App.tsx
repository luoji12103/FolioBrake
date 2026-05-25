import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Suspense, lazy } from "react";
import Layout from "./components/Layout";
import { ErrorBoundary } from "./components/ErrorBoundary";

const Dashboard = lazy(() => import("./pages/Dashboard"));
const Universe = lazy(() => import("./pages/Universe"));
const Signals = lazy(() => import("./pages/Signals"));
const Risk = lazy(() => import("./pages/Risk"));
const Backtest = lazy(() => import("./pages/Backtest"));
const Audit = lazy(() => import("./pages/Audit"));
const Paper = lazy(() => import("./pages/Paper"));
const Settings = lazy(() => import("./pages/Settings"));

function PageLoader() {
  return <div style={{ display: "flex", justifyContent: "center", padding: 48 }}><div style={{ width: 200, height: 24, borderRadius: 6, background: "linear-gradient(90deg, var(--color-surface) 25%, var(--color-border) 50%, var(--color-surface) 75%)", backgroundSize: "200% 100%", animation: "shimmer 1.5s ease-in-out infinite" }} /></div>;
}

function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<Suspense fallback={<PageLoader />}><Dashboard /></Suspense>} />
            <Route path="/universe" element={<Suspense fallback={<PageLoader />}><Universe /></Suspense>} />
            <Route path="/signals" element={<Suspense fallback={<PageLoader />}><Signals /></Suspense>} />
            <Route path="/risk" element={<Suspense fallback={<PageLoader />}><Risk /></Suspense>} />
            <Route path="/backtest" element={<Suspense fallback={<PageLoader />}><Backtest /></Suspense>} />
            <Route path="/audit" element={<Suspense fallback={<PageLoader />}><Audit /></Suspense>} />
            <Route path="/paper" element={<Suspense fallback={<PageLoader />}><Paper /></Suspense>} />
            <Route path="/settings" element={<Suspense fallback={<PageLoader />}><Settings /></Suspense>} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
