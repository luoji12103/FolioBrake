import { useState, useEffect, useRef, useMemo, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { displayShortcut } from "../hooks/useKeyboardShortcuts";
import api from "../api/client";
import "./CommandPalette.css";

interface Command {
  id: string;
  label: string;
  sublabel?: string;
  shortcut?: string;
  section: string;
  action: () => void;
}

interface SearchResult {
  id: string;
  symbol: string;
  name: string;
  type: string;
}

interface CommandPaletteProps {
  open: boolean;
  onClose: () => void;
  onToggleTheme: () => void;
}

export function CommandPalette({ open, onClose, onToggleTheme }: CommandPaletteProps) {
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const navigate = useNavigate();

  const commands: Command[] = useMemo(
    () => [
      { id: "nav-dashboard", label: "Go to Dashboard", shortcut: "G+D", section: "Navigation", action: () => navigate("/") },
      { id: "nav-universe", label: "Go to Universe", shortcut: "G+U", section: "Navigation", action: () => navigate("/universe") },
      { id: "nav-signals", label: "Go to Signals", shortcut: "G+S", section: "Navigation", action: () => navigate("/signals") },
      { id: "nav-risk", label: "Go to Risk Overlay", shortcut: "G+R", section: "Navigation", action: () => navigate("/risk") },
      { id: "nav-backtest", label: "Go to Backtest", shortcut: "G+B", section: "Navigation", action: () => navigate("/backtest") },
      { id: "nav-audit", label: "Go to Audit", shortcut: "G+A", section: "Navigation", action: () => navigate("/audit") },
      { id: "nav-paper", label: "Go to Paper Portfolio", shortcut: "G+P", section: "Navigation", action: () => navigate("/paper") },
      { id: "nav-settings", label: "Go to Settings", shortcut: "G+.", section: "Navigation", action: () => navigate("/settings") },
      { id: "theme-toggle", label: "Toggle Theme", shortcut: "Ctrl+Shift+L", section: "Actions", action: onToggleTheme },
      { id: "close-palette", label: "Close Command Palette", shortcut: "Escape", section: "Actions", action: onClose },
    ],
    [navigate, onClose, onToggleTheme]
  );

  const doSearch = useCallback(async (q: string) => {
    if (q.length < 2) {
      setSearchResults([]);
      return;
    }
    setSearchLoading(true);
    try {
      const { data } = await api.get("/data/instruments", { params: { search: q } });
      const items: SearchResult[] = (Array.isArray(data) ? data : []).slice(0, 8).map((i: any) => ({
        id: String(i.id ?? i.symbol),
        symbol: i.symbol,
        name: i.name,
        type: i.type ?? "ETF",
      }));
      setSearchResults(items);
    } catch {
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!open) return;
    const timer = setTimeout(() => doSearch(query), 250);
    return () => clearTimeout(timer);
  }, [query, open, doSearch]);

  const filtered = useMemo(() => {
    if (!query) return commands;
    const q = query.toLowerCase();
    return commands.filter(
      (c) =>
        c.label.toLowerCase().includes(q) ||
        c.section.toLowerCase().includes(q)
    );
  }, [commands, query]);

  const instrumentCommands: Command[] = useMemo(() => {
    return searchResults.map((r) => ({
      id: `instr-${r.id}`,
      label: `${r.symbol} — ${r.name}`,
      sublabel: r.type,
      section: "Instruments",
      action: () => navigate(`/universe?search=${r.symbol}`),
    }));
  }, [searchResults, navigate]);

  const allItems = useMemo(() => {
    const items: Command[] = [...filtered, ...instrumentCommands];
    return items;
  }, [filtered, instrumentCommands]);

  const grouped = useMemo(() => {
    const groups: Record<string, Command[]> = {};
    for (const cmd of allItems) {
      if (!groups[cmd.section]) groups[cmd.section] = [];
      groups[cmd.section].push(cmd);
    }
    return groups;
  }, [allItems]);

  useEffect(() => {
    if (open) {
      setQuery("");
      setSelectedIndex(0);
      requestAnimationFrame(() => inputRef.current?.focus());
    }
  }, [open]);

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  useEffect(() => {
    if (!open) return;
    const el = listRef.current?.querySelector(`[data-index="${selectedIndex}"]`);
    el?.scrollIntoView({ block: "nearest" });
  }, [selectedIndex, open]);

  const executeCommand = (cmd: Command) => {
    onClose();
    requestAnimationFrame(() => cmd.action());
  };

  if (!open) return null;

  const flatList = allItems;

  return (
    <div className="palette-backdrop" onClick={onClose}>
      <div className="palette" onClick={(e) => e.stopPropagation()}>
        <div className="palette-input-wrap">
          <svg className="palette-search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            ref={inputRef}
            className="palette-input"
            placeholder="Search commands or instruments..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "ArrowDown") {
                e.preventDefault();
                setSelectedIndex((i) => Math.min(i + 1, flatList.length - 1));
              } else if (e.key === "ArrowUp") {
                e.preventDefault();
                setSelectedIndex((i) => Math.max(i - 1, 0));
              } else if (e.key === "Enter" && flatList[selectedIndex]) {
                executeCommand(flatList[selectedIndex]);
              } else if (e.key === "Escape") {
                onClose();
              }
            }}
          />
          <kbd className="palette-esc">Esc</kbd>
        </div>

        <div className="palette-list" ref={listRef}>
          {searchLoading && query.length >= 2 && (
            <div className="palette-empty">Searching instruments...</div>
          )}
          {flatList.length === 0 && !searchLoading && (
            <div className="palette-empty">No results found</div>
          )}
          {Object.entries(grouped).map(([section, cmds]) => (
            <div key={section} className="palette-section">
              <div className="palette-section-label">{section}</div>
              {cmds.map((cmd) => {
                const idx = flatList.indexOf(cmd);
                return (
                  <div
                    key={cmd.id}
                    className={`palette-item ${idx === selectedIndex ? "palette-item-active" : ""}`}
                    data-index={idx}
                    onClick={() => executeCommand(cmd)}
                    onMouseEnter={() => setSelectedIndex(idx)}
                  >
                    <div className="palette-item-text">
                      <span className="palette-item-label">{cmd.label}</span>
                      {cmd.sublabel && (
                        <span className="palette-item-sublabel">{cmd.sublabel}</span>
                      )}
                    </div>
                    {cmd.shortcut && (
                      <span className="palette-item-shortcut">
                        {displayShortcut(cmd.shortcut)}
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
