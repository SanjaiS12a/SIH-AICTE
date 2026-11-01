import { Component } from "react";
import type { ErrorInfo, ReactNode } from "react";
import { useLocation } from "react-router-dom";

class Boundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Page could not render", error, info.componentStack);
  }
  render() {
    return this.state.failed ? (
      <section className="panel card-body" role="alert">
        <h1>This page could not be displayed</h1>
        <p>
          Your navigation is still available. Retry the page or open another
          section.
        </p>
        <button onClick={() => this.setState({ failed: false })}>
          Retry page
        </button>
      </section>
    ) : (
      this.props.children
    );
  }
}
export function PageBoundary({ children }: { children: ReactNode }) {
  const location = useLocation();
  return (
    <Boundary key={location.pathname + location.search}>{children}</Boundary>
  );
}
