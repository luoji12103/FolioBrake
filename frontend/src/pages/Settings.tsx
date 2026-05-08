import { useState, useEffect } from "react";
import {
  useStrategyConfigs,
  StrategyConfigEntry,
  createStrategyConfig,
  updateStrategyConfig,
  deleteStrategyConfig,
  useUserPreferences,
} from "../api/hooks";
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

function StrategyConfigSection() {
  const { data: configs, isLoading, refetch } = useStrategyConfigs();
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [editingParams, setEditingParams] = useState("");
  const [editingName, setEditingName] = useState("");
  const [editingVersion, setEditingVersion] = useState("v1");
  const [editingRiskProfile, setEditingRiskProfile] = useState("balanced");
  const [isCreating, setIsCreating] = useState(false);
  const [toast, setToast] = useState<{ type: "success" | "error"; msg: string } | null>(null);
  const [jsonError, setJsonError] = useState<string | null>(null);

  const selected = configs?.find((c) => c.id === selectedId) ?? null;

  const showToast = (type: "success" | "error", msg: string) => {
    setToast({ type, msg });
    setTimeout(() => setToast(null), 3000);
  };

  const startCreate = () => {
    setIsCreating(true);
    setSelectedId(null);
    setEditingName("");
    setEditingVersion("v1");
    setEditingRiskProfile("balanced");
    setEditingParams(JSON.stringify({ max_holdings: 5, max_concentration: 0.30, min_positions: 3, max_turnover: 0.50 }, null, 2));
    setJsonError(null);
  };

  const startEdit = (config: StrategyConfigEntry) => {
    setIsCreating(false);
    setSelectedId(config.id);
    setEditingName(config.name);
    setEditingVersion(config.version);
    setEditingRiskProfile(config.risk_profile);
    setEditingParams(JSON.stringify(config.parameters, null, 2));
    setJsonError(null);
  };

  const handleSave = async () => {
    let parsed: Record<string, any>;
    try {
      parsed = JSON.parse(editingParams);
      setJsonError(null);
    } catch {
      setJsonError("Invalid JSON");
      return;
    }

    try {
      if (isCreating) {
        await createStrategyConfig({
          name: editingName || "untitled",
          version: editingVersion,
          parameters: parsed,
          risk_profile: editingRiskProfile,
        });
        showToast("success", "Config created");
      } else if (selectedId) {
        await updateStrategyConfig(selectedId, {
          name: editingName,
          version: editingVersion,
          parameters: parsed,
          risk_profile: editingRiskProfile,
        });
        showToast("success", "Config updated");
      }
      setIsCreating(false);
      setSelectedId(null);
      refetch();
    } catch (err: any) {
      showToast("error", err?.response?.data?.detail || "Save failed");
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteStrategyConfig(id);
      showToast("success", "Config deleted");
      if (selectedId === id) {
        setSelectedId(null);
        setIsCreating(false);
      }
      refetch();
    } catch (err: any) {
      showToast("error", err?.response?.data?.detail || "Delete failed");
    }
  };

  if (isLoading) {
    return (
      <div className="card">
        <div className="card-title">Strategy Configuration</div>
        <div className="skeleton" style={{ height: 36, width: "100%", marginBottom: "var(--space-3)" }} />
        <div className="skeleton" style={{ height: 36, width: "60%" }} />
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-title">Strategy Configuration</div>
      <p style={{ fontSize: "var(--text-sm)", color: "var(--color-text-muted)", marginBottom: "var(--space-4)" }}>
        Manage strategy parameter presets. Select a config to edit, or create a new one.
      </p>

      <div style={{ display: "flex", gap: "var(--space-4)", flexWrap: "wrap", alignItems: "flex-start" }}>
        <div style={{ minWidth: 260, flex: "0 0 auto" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-3)" }}>
            <span style={{ fontSize: "var(--text-sm)", fontWeight: 600, color: "var(--color-text-muted)" }}>
              Saved Configs ({configs?.length ?? 0})
            </span>
            <button className="btn btn-secondary" style={{ fontSize: "var(--text-xs)", padding: "4px 10px" }} onClick={startCreate}>
              + New
            </button>
          </div>

          {(!configs || configs.length === 0) ? (
            <div style={{ padding: "var(--space-4)", background: "var(--color-surface-raised)", borderRadius: "var(--radius-md)", textAlign: "center", color: "var(--color-text-dim)", fontSize: "var(--text-sm)" }}>
              No configs yet. Create one to get started.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
              {configs.map((c) => (
                <div
                  key={c.id}
                  onClick={() => startEdit(c)}
                  style={{
                    padding: "var(--space-3)",
                    background: selectedId === c.id && !isCreating ? "var(--color-accent-dim)" : "var(--color-surface-raised)",
                    border: `1px solid ${selectedId === c.id && !isCreating ? "var(--color-accent)" : "var(--color-border-subtle)"}`,
                    borderRadius: "var(--radius-md)",
                    cursor: "pointer",
                    transition: "all var(--duration-fast)",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontWeight: 600, fontSize: "var(--text-sm)", color: "var(--color-text)" }}>{c.name}</span>
                    <span className="badge" style={{ fontSize: "var(--text-xs)" }}>{c.version}</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "var(--space-1)" }}>
                    <span style={{ fontSize: "var(--text-xs)", color: "var(--color-text-dim)" }}>
                      {c.risk_profile} · {Object.keys(c.parameters).length} params
                    </span>
                    <button
                      className="btn"
                      style={{ fontSize: "var(--text-xs)", padding: "2px 8px", color: "var(--color-red)", background: "transparent" }}
                      onClick={(e) => { e.stopPropagation(); handleDelete(c.id); }}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {(selected || isCreating) && (
          <div style={{ flex: 1, minWidth: 300 }}>
            <div style={{ fontSize: "var(--text-sm)", fontWeight: 600, color: "var(--color-text-muted)", marginBottom: "var(--space-3)" }}>
              {isCreating ? "New Configuration" : `Editing: ${selected?.name}`}
            </div>

            <div className="form-group">
              <label htmlFor="cfg-name">Name</label>
              <input
                id="cfg-name"
                className="form-input"
                value={editingName}
                onChange={(e) => setEditingName(e.target.value)}
                placeholder="e.g. conservative_v2"
              />
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-3)" }}>
              <div className="form-group">
                <label htmlFor="cfg-version">Version</label>
                <input
                  id="cfg-version"
                  className="form-input"
                  value={editingVersion}
                  onChange={(e) => setEditingVersion(e.target.value)}
                  placeholder="v1"
                />
              </div>
              <div className="form-group">
                <label htmlFor="cfg-risk">Risk Profile</label>
                <select
                  id="cfg-risk"
                  className="form-input"
                  value={editingRiskProfile}
                  onChange={(e) => setEditingRiskProfile(e.target.value)}
                >
                  <option value="conservative">Conservative</option>
                  <option value="balanced">Balanced</option>
                  <option value="aggressive">Aggressive</option>
                </select>
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="cfg-params">Parameters (JSON)</label>
              <textarea
                id="cfg-params"
                className="form-input"
                rows={10}
                value={editingParams}
                onChange={(e) => { setEditingParams(e.target.value); setJsonError(null); }}
                style={{ fontFamily: "var(--font-mono)", fontSize: "var(--text-sm)", resize: "vertical" }}
                placeholder='{ "max_holdings": 5 }'
              />
              {jsonError && (
                <p style={{ fontSize: "var(--text-xs)", color: "var(--color-red)", marginTop: "var(--space-1)" }}>
                  {jsonError}
                </p>
              )}
            </div>

            <div style={{ display: "flex", gap: "var(--space-2)", marginTop: "var(--space-2)" }}>
              <button className="btn btn-primary" onClick={handleSave}>
                {isCreating ? "Create Config" : "Save Changes"}
              </button>
              <button
                className="btn"
                onClick={() => { setSelectedId(null); setIsCreating(false); setJsonError(null); }}
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>

      {toast && (
        <span className={`toast toast-${toast.type}`} style={{ marginTop: "var(--space-3)" }}>
          {toast.type === "success" ? "\u2713" : "\u2717"} {toast.msg}
        </span>
      )}
    </div>
  );
}

function NotificationPreferencesCard() {
  const { preferences, update } = useUserPreferences();
  const notifs = preferences.notifications;

  const toggle = (key: keyof typeof notifs) => {
    update({ notifications: { ...notifs, [key]: !notifs[key] } });
  };

  const items: { key: keyof typeof notifs; label: string; desc: string }[] = [
    { key: "riskAlerts", label: "Risk Alerts", desc: "Drawdown, volatility, and regime changes" },
    { key: "signalAlerts", label: "Signal Alerts", desc: "New signals and score changes" },
    { key: "tradeAlerts", label: "Trade Alerts", desc: "Order fills and portfolio rebalancing" },
    { key: "systemAlerts", label: "System Alerts", desc: "Data source health and connectivity" },
  ];

  return (
    <div className="card">
      <div className="card-title">Notification Preferences</div>
      <p style={{ fontSize: "var(--text-sm)", color: "var(--color-text-muted)", marginBottom: "var(--space-4)" }}>
        Choose which notification categories appear in your alerts panel.
      </p>
      <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)", maxWidth: 500 }}>
        {items.map((item) => (
          <label
            key={item.key}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "var(--space-3)",
              background: "var(--color-surface-raised)",
              borderRadius: "var(--radius-md)",
              cursor: "pointer",
            }}
          >
            <div>
              <div style={{ fontSize: "var(--text-sm)", fontWeight: 600, color: "var(--color-text)" }}>
                {item.label}
              </div>
              <div style={{ fontSize: "var(--text-xs)", color: "var(--color-text-dim)", marginTop: 2 }}>
                {item.desc}
              </div>
            </div>
            <button
              role="switch"
              aria-checked={notifs[item.key]}
              onClick={() => toggle(item.key)}
              style={{
                width: 40,
                height: 22,
                borderRadius: "var(--radius-full)",
                border: "none",
                background: notifs[item.key] ? "var(--color-accent)" : "var(--color-border)",
                position: "relative",
                cursor: "pointer",
                transition: "background var(--duration-fast)",
                flexShrink: 0,
              }}
            >
              <span
                style={{
                  position: "absolute",
                  top: 3,
                  left: notifs[item.key] ? 20 : 3,
                  width: 16,
                  height: 16,
                  borderRadius: "50%",
                  background: "var(--color-surface)",
                  transition: "left var(--duration-fast) var(--ease-out)",
                  boxShadow: "var(--shadow-sm)",
                }}
              />
            </button>
          </label>
        ))}
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

      <NotificationPreferencesCard />

      <StrategyConfigSection />

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
