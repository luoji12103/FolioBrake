interface ChartOverlayProps {
  visible: boolean;
  children: React.ReactNode;
  onClose?: () => void;
}

export function ChartOverlay({ visible, children, onClose }: ChartOverlayProps) {
  if (!visible) return null;
  
  return (
    <div style={{ position: "absolute", inset: 0, background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 10 }}
      onClick={onClose}>
      <div onClick={(e) => e.stopPropagation()}>
        {children}
      </div>
    </div>
  );
}
