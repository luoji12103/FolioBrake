import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Universe from "./pages/Universe";
import Signals from "./pages/Signals";
import Risk from "./pages/Risk";
import Backtest from "./pages/Backtest";
import Audit from "./pages/Audit";
import Paper from "./pages/Paper";
import Settings from "./pages/Settings";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/universe" element={<Universe />} />
          <Route path="/signals" element={<Signals />} />
          <Route path="/risk" element={<Risk />} />
          <Route path="/backtest" element={<Backtest />} />
          <Route path="/audit" element={<Audit />} />
          <Route path="/paper" element={<Paper />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
