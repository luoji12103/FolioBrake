import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import "./LoadingBar.css";

export function LoadingBar() {
  const location = useLocation();
  const [active, setActive] = useState(false);

  useEffect(() => {
    setActive(true);
    const timer = setTimeout(() => setActive(false), 350);
    return () => clearTimeout(timer);
  }, [location.pathname]);

  if (!active) return null;

  return (
    <div className="loading-bar-track">
      <div className="loading-bar-fill" />
    </div>
  );
}
