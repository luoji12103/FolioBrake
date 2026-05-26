interface ChartInteractionProps {
  children: React.ReactNode;
  onHover?: (index: number) => void;
  onClick?: (index: number) => void;
}

export function ChartInteraction({ children, onHover, onClick }: ChartInteractionProps) {
  return (
    <div style={{ position: "relative" }}
      onMouseMove={(e) => {
        const rect = e.currentTarget.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const index = Math.floor((x / rect.width) * 100);
        onHover?.(index);
      }}
      onClick={(e) => {
        const rect = e.currentTarget.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const index = Math.floor((x / rect.width) * 100);
        onClick?.(index);
      }}>
      {children}
    </div>
  );
}
