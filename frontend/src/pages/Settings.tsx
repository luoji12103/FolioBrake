import { useState, useEffect } from "react";
import "./shared.css";

interface SettingsState {
  riskProfile: "conservative" | "balanced" | "aggressive";
  apiUrl: string;
  dataSource: "akshare" | "tushare";
}

const defaultSettings: SettingsState = {
  riskProfile: "balanced",
  apiUrl: "http://localhost:8000",
  dataSource: "akshare",
};

const PROFILE_DESCRIPTIONS: Record<SettingsState["riskProfile"], string> = {
  conservative:
    "Prioritizes capital preservation. Lower position sizes, wider stops, and preference for low-volatility ETFs.",
  balanced:
    "Moderate risk-reward balance. Standard position sizing with sector diversification.",
  aggressive:
    "Maximizes return potential. Higher position sizes, tighter stops, and momentum-focused selection.",
};

const PROFILE_ICONS: Record<SettingsState["riskProfile"], string> = {
  conservative: "\uD83D\uDEE1",
  balanced: "\u2696",
  aggressive: "\uD83D\uDD25",
};

const STORAGE_KEY = "folioBrake_settings";

function loadSettings(): SettingsState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      return { ...defaultSettings, ...parsed };
    }
  } catch {
    /* ignore */
  }
  return defaultSettings;
}

function saveSettings(settings: SettingsState) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  } catch {
    /* ignore */
  }
}

function SettingsSkeleton() {
  return (
    <div style={{ marginTop: "var(--space-4)" }}>
      <div className="skeleton-card">
        <div className="skeleton" style={{ height: 12, width: "30%", marginBottom: "var(--space-3)" }} />
        <div className="skeleton" style={{ height: 42, width: "100%", marginBottom: "var(--space-3)" }} />
        <div className="skeleton" style={{ height: 14, width: "70%" }} />
      </div>
      <div className="skeleton-card">
        <div className="skeleton" style={{ height: 12, width: "30%", marginBottom: "var(--space-3)" }} />
        <div className="skeleton" style={{ height: 42, width: "100%" }} />
      </div>
    </div>
  );
}

function Settings() {
  const [isInitialized, setIsInitialized] = useState(false);
  const [settings, setSettings] = useState<SettingsState>(defaultSettings);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setSettings(loadSettings());
    setIsInitialized(true);
  }, []);

  const update = <K extends keyof SettingsState>(
    key: K,
    value: SettingsState[K]
  ) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
    setSaved(false);
  };

  const handleSave = () => {
    saveSettings(settings);
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  if (!isInitialized) {
    return (
      <div className="page">
        <h2>Settings</h2>
        <SettingsSkeleton />
      </div>
    );
  }

  return (
    <div className="page">
      <h2>Settings</h2>

      <div className="card">
        <div className="card-title">Risk Profile</div>
        <div style={{ maxWidth: 500 }}>
          <div className="form-group">
            <label htmlFor="settings-profile">Profile</label>
            <select
              id="settings-profile"
              className="form-input"
              value={settings.riskProfile}
              onChange={(e) =>
                update(
                  "riskProfile",
                  e.target.value as SettingsState["riskProfile"]
                )
              }
            >
              <option value="conservative">Conservative</option>
              <option value="balanced">Balanced</option>
              <option value="aggressive">Aggressive</option>
            </select>
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "flex-start",
              gap: "var(--space-3)",
              padding: "var(--space-3)",
              background: "var(--color-surface-raised)",
              borderRadius: "var(--radius-md)",
              marginTop: "var(--space-1)",
            }}
          >
            <span style={{ fontSize: 20, lineHeight: 1 }}>
              {PROFILE_ICONS[settings.riskProfile]}
            </span>
            <p
              style={{
                fontSize: "var(--text-sm)",
                color: "var(--color-text-muted)",
                lineHeight: "var(--leading-relaxed)",
              }}
            >
              {PROFILE_DESCRIPTIONS[settings.riskProfile]}
            </p>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-title">Backend Connection</div>
        <div style={{ maxWidth: 500 }}>
          <div className="form-group">
            <label htmlFor="settings-api">API Base URL</label>
            <input
              id="settings-api"
              className="form-input"
              type="url"
              value={settings.apiUrl}
              onChange={(e) => update("apiUrl", e.target.value)}
              placeholder="http://localhost:8000"
            />
          </div>
          <p
            style={{
              fontSize: "var(--text-xs)",
              color: "var(--color-text-dim)",
              marginTop: "var(--space-1)",
            }}
          >
            Changing the API URL requires a page refresh to take effect.
          </p>
        </div>
      </div>

      <div className="card">
        <div className="card-title">Market Data Source</div>
        <div style={{ maxWidth: 500 }}>
          <div className="form-group">
            <label htmlFor="settings-source">Data Provider</label>
            <select
              id="settings-source"
              className="form-input"
              value={settings.dataSource}
              onChange={(e) =>
                update(
                  "dataSource",
                  e.target.value as SettingsState["dataSource"]
                )
              }
            >
              <option value="akshare">AKShare (Free)</option>
              <option value="tushare">Tushare (Token Required)</option>
            </select>
          </div>
          <p
            style={{
              fontSize: "var(--text-xs)",
              color: "var(--color-text-dim)",
              marginTop: "var(--space-1)",
            }}
          >
            AKShare is the default open-source Chinese market data provider.
            Tushare requires an API token and may have rate limits.
          </p>
        </div>
      </div>

      <div className="card">
        <div className="card-title">Appearance</div>
        <div style={{ maxWidth: 500 }}>
          <div className="form-group">
            <label htmlFor="settings-theme">Theme</label>
            <select
              id="settings-theme"
              className="form-input"
              value={localStorage.getItem("folioBrake_theme") || "auto"}
              onChange={(e) => {
                const val = e.target.value;
                localStorage.setItem("folioBrake_theme", val);
                if (val === "light") document.documentElement.setAttribute("data-theme", "light");
                else if (val === "dark") document.documentElement.setAttribute("data-theme", "dark");
                else document.documentElement.removeAttribute("data-theme");
              }}
            >
              <option value="auto">System (Auto)</option>
              <option value="light">Light</option>
              <option value="dark">Dark</option>
            </select>
          </div>
        </div>
      </div>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "var(--space-3)",
          marginTop: "var(--space-2)",
        }}
      >
        <button className="btn btn-primary" onClick={handleSave}>
          Save Settings
        </button>
        {saved && (
          <span className="toast toast-success">
            {"\u2713"} Saved successfully
          </span>
        )}
      </div>
    </div>
  );
}

export default Settings;
