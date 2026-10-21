import { Component, ErrorInfo, ReactNode } from "react";
import { Button } from "./Button";

export interface ErrorBoundaryProps {
  children: ReactNode;
  fallbackTitle?: string;
}

export interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

export class EnterpriseErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  override componentDidCatch(_error: Error, _errorInfo: ErrorInfo) { }

  override render() {
    if (this.state.hasError) {
      return (
        <div role="alert" className="p-5 border border-rose-500/40 bg-rose-950/30 rounded-2xl text-left space-y-2">
          <h4 className="font-bold text-sm text-rose-300">
            {this.props.fallbackTitle || "Error al renderizar el panel"}
          </h4>
          <p className="text-xs text-rose-200">
            El componente ha experimentado una excepción aislada. El resto de la aplicación continúa operativo.
          </p>
          <Button
            size="sm"
            variant="outline"
            onClick={() => this.setState({ hasError: false })}
          >
            Recargar panel
          </Button>
        </div>
      );
    }
    return this.props.children;
  }
}
