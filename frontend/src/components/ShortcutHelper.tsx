import { displayShortcut } from "../hooks/useKeyboardShortcuts";
import "./ShortcutHelper.css";

interface ShortcutDef {
  combo: string;
  label: string;
}

interface ShortcutHelperProps {
  open: boolean;
  onClose: () => void;
}

const SHORTCUTS: { section: string; items: ShortcutDef[] }[] = [
  {
    section: "Global",
    items: [
      { combo: "Ctrl+K", label: "Open command palette" },
      { combo: "Shift+/", label: "Show keyboard shortcuts" },
      { combo: "Ctrl+Shift+L", label: "Toggle theme" },
      { combo: "Escape", label: "Close overlay / blur input" },
    ],
  },
  {
    section: "Navigation",
    items: [
      { combo: "G+D", label: "Dashboard" },
      { combo: "G+U", label: "Universe" },
      { combo: "G+S", label: "Signals" },
      { combo: "G+R", label: "Risk Overlay" },
      { combo: "G+B", label: "Backtest" },
      { combo: "G+A", label: "Audit" },
      { combo: "G+P", label: "Paper Portfolio" },
      { combo: "G+.", label: "Settings" },
    ],
  },
  {
    section: "Page Actions",
    items: [
      { combo: "Ctrl+Shift+R", label: "Refresh current data" },
    ],
  },
];

export function ShortcutHelper({ open, onClose }: ShortcutHelperProps) {
  if (!open) return null;

  return (
    <div className="shortcut-backdrop" onClick={onClose}>
      <div className="shortcut-modal" onClick={(e) => e.stopPropagation()}>
        <div className="shortcut-header">
          <h3>Keyboard Shortcuts</h3>
          <button className="shortcut-close" onClick={onClose}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <div className="shortcut-body">
          {SHORTCUTS.map((group) => (
            <div key={group.section} className="shortcut-group">
              <div className="shortcut-group-label">{group.section}</div>
              {group.items.map((item) => (
                <div key={item.combo} className="shortcut-row">
                  <span className="shortcut-desc">{item.label}</span>
                  <span className="shortcut-keys">
                    {displayShortcut(item.combo)
                      .split(/(\u2318|\u21E7|\u2325)/)
                      .map((part, i) => (
                        <kbd key={i} className="kbd-key">{part}</kbd>
                      ))}
                  </span>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
