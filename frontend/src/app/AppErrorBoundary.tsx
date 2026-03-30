import { Component, type ErrorInfo, type ReactNode } from "react";

type AppErrorBoundaryProps = {
  children: ReactNode;
};

type AppErrorBoundaryState = {
  error: Error | null;
  componentStack: string;
};

export class AppErrorBoundary extends Component<AppErrorBoundaryProps, AppErrorBoundaryState> {
  state: AppErrorBoundaryState = {
    error: null,
    componentStack: ""
  };

  static getDerivedStateFromError(error: Error): AppErrorBoundaryState {
    return {
      error,
      componentStack: ""
    };
  }

  override componentDidCatch(error: Error, info: ErrorInfo) {
    this.setState({
      error,
      componentStack: info.componentStack ?? ""
    });
  }

  override render() {
    if (!this.state.error) {
      return this.props.children;
    }

    return (
      <main className="screen">
        <section className="card auth-card">
          <p className="eyebrow">MotionLab</p>
          <h1>Сталася помилка під час запуску фронтенда</h1>
          <p className="muted">{this.state.error.message}</p>
          {this.state.componentStack ? (
            <pre className="error-trace">{this.state.componentStack.trim()}</pre>
          ) : null}
        </section>
      </main>
    );
  }
}
