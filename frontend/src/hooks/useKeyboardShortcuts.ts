import { useEffect, useRef } from "react";

function normaliseEvent(e: KeyboardEvent): string {
  const parts: string[] = [];
  if (e.ctrlKey || e.metaKey) parts.push("Ctrl");
  if (e.shiftKey) parts.push("Shift");
  if (e.altKey) parts.push("Alt");

  const key = e.key;
  if (["Control", "Shift", "Alt", "Meta"].includes(key)) return "";
  parts.push(key.length === 1 ? key.toUpperCase() : key);
  return parts.join("+");
}

export interface ShortcutMap {
  [combo: string]: () => void;
}

export function useKeyboardShortcuts(shortcuts: ShortcutMap) {
  const shortcutsRef = useRef(shortcuts);
  shortcutsRef.current = shortcuts;

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      const tag = target.tagName;
      if (
        tag === "INPUT" ||
        tag === "TEXTAREA" ||
        tag === "SELECT" ||
        target.isContentEditable
      ) {
        if (e.key !== "Escape") return;
      }

      const combo = normaliseEvent(e);
      if (!combo) return;

      const cb = shortcutsRef.current[combo];
      if (cb) {
        e.preventDefault();
        e.stopPropagation();
        cb();
      }
    };

    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);
}

export function isMac(): boolean {
  return typeof navigator !== "undefined" && /Mac/i.test(navigator.userAgent);
}

export function displayShortcut(combo: string): string {
  if (!isMac()) return combo;
  return combo
    .replace(/Ctrl\+/g, "\u2318")
    .replace(/Shift\+/g, "\u21E7")
    .replace(/Alt\+/g, "\u2325");
}
