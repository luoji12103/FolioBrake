import { useState, useEffect } from "react";
import "./shared.css";

/* ---- Types ---- */

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

const STORAGE_KEY = "folioBrake_settings";

/* ---- Load persisted settings ---- */

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

/* ---- Skeleton ---- */

function SettingsSkeleton() {
  return (
    <div style={{ marginTop: 16 }}>
      <div className="skeleton" style={{ height: 200, marginBottom: 20 }} />
    </div>
  );
}

/* ---- Page ---- */

function Settings() {
  const [isInitialized, setIsInitialized] = useState(false);
  const [settings, setSettings] = useState<SettingsState>(defaultSettings);
  const [saved, setSaved] = useState(false);

  /* Load on mount */
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

      {/* Risk Profile */}
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
          <p
            style={{
              fontSize: 13,
              color: "var(--color-text-muted)",
              lineHeight: 1.6,
              marginTop: 4,
            }}
          >
            {PROFILE_DESCRIPTIONS[settings.riskProfile]}
          </p>
        </div>
      </div>

      {/* API URL */}
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
              fontSize: 12,
              color: "var(--color-text-muted)",
              marginTop: 4,
            }}
          >
            Changing the API URL requires a page refresh to take effect.
          </p>
        </div>
      </div>

      {/* Data Source */}
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
              fontSize: 12,
              color: "var(--color-text-muted)",
              marginTop: 4,
            }}
          >
            AKShare is the default open-source Chinese market data provider.
            Tushare requires an API token and may have rate limits.
          </p>
        </div>
      </div>

      {/* Save */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          marginTop: 8,
        }}
      >
        <button className="btn btn-primary" onClick={handleSave}>
          Save Settings
        </button>
        {saved && (
          <span
            style={{
              fontSize: 13,
              color: "var(--color-green)",
              fontWeight: 600,
            }}
          >
            Saved successfully
          </span>
        )}
      </div>
    </div>
  );
}

export default Settings;
