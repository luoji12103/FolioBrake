import { ReactNode } from "react";

interface SettingsSectionProps {
  title: string;
  description?: string;
  children: ReactNode;
}

export function SettingsSection({ title, description, children }: SettingsSectionProps) {
  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div className="card-title">{title}</div>
      {description && <p style={{ color: "var(--color-text-muted)", fontSize: 14, marginBottom: 16 }}>{description}</p>}
      {children}
    </div>
  );
}
