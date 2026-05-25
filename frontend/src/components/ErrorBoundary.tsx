import { Component, ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("ErrorBoundary caught:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div style={{ padding: 24, textAlign: "center", color: "var(--color-text)" }}>
            <h2>Something went wrong</h2>
            <p style={{ color: "var(--color-text-muted)", marginTop: 8 }}>
              {this.state.error?.message || "An unexpected error occurred"}
            </p>
            <button className="btn-primary" onClick={() => this.setState({ hasError: false, error: null })} style={{ marginTop: 16 }}>
              Try Again
            </button>
          </div>
        )
      );
    }
    return this.props.children;
  }
}
