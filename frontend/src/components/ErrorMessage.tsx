interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorMessage({ message, onRetry }: ErrorMessageProps) {
  return (
    <div className="state-banner state-error">
      <div className="state-error-icon">⚠️</div>
      <div className="state-error-title">Error</div>
      <div className="state-error-desc">{message}</div>
      {onRetry && <button className="btn-primary" onClick={onRetry} style={{ marginTop: 8 }}>Retry</button>}
    </div>
  );
}
