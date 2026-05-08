import { displayShortcut } from "../hooks/useKeyboardShortcuts";

export function Kbd({ combo }: { combo: string }) {
  const parts = displayShortcut(combo).split(/(\u2318|\u21E7|\u2325)/);
  return (
    <span className="kbd-hint">
      {parts.map((part, i) => (
        <kbd key={i} className="kbd-key">{part}</kbd>
      ))}
    </span>
  );
}
