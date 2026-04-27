import { useEffect, useState } from "react";
import { healthCheck } from "../api/client";

function Dashboard() {
  const [health, setHealth] = useState<{ status: string; version: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    healthCheck()
      .then(setHealth)
      .catch((err) => setError(err.message));
  }, []);

  return (
    <div>
      <h2>Dashboard</h2>
      <div style={{ marginTop: 16 }}>
        {error && <p style={{ color: "var(--color-red)" }}>Backend connection error: {error}</p>}
        {health && (
          <p style={{ color: "var(--color-green)" }}>
            Backend: {health.status} (v{health.version})
          </p>
        )}
        {!health && !error && <p>Connecting to backend...</p>}
      </div>
    </div>
  );
}

export default Dashboard;
