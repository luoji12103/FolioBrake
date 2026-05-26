interface SuccessMessageProps {
  message: string;
}

export function SuccessMessage({ message }: SuccessMessageProps) {
  return (
    <div className="state-banner state-success">
      <div className="state-success-icon">✅</div>
      <div className="state-success-title">Success</div>
      <div className="state-success-desc">{message}</div>
    </div>
  );
}
