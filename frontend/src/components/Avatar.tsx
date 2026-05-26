interface AvatarProps {
  name: string;
  size?: number;
}

export function Avatar({ name, size = 32 }: AvatarProps) {
  const initials = name.split(" ").map(w => w[0]).join("").toUpperCase().slice(0, 2);
  const colors = ["#4f8cff", "#34d399", "#fbbf24", "#f87171", "#8b5cf6"];
  const color = colors[name.length % colors.length];
  
  return (
    <div style={{ width: size, height: size, borderRadius: "50%", background: color, display: "flex", alignItems: "center", justifyContent: "center", color: "#fff", fontSize: size * 0.4, fontWeight: 600 }}>
      {initials}
    </div>
  );
}
