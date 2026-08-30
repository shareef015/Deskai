"use client";

import React from "react";

interface Props {
  readonly boundary: string;
  readonly children: React.ReactNode;
  readonly onError?: (error: Error, boundary: string) => void;
}

interface State {
  readonly error: Error | null;
}

export class OperatorErrorBoundary extends React.Component<Props, State> {
  override state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  override componentDidCatch(error: Error): void {
    this.props.onError?.(error, this.props.boundary);
  }

  override render(): React.ReactNode {
    if (this.state.error) {
      return (
        <section role="alert" aria-labelledby={`${this.props.boundary}-error-title`}>
          <h2 id={`${this.props.boundary}-error-title`}>This workspace section could not be loaded</h2>
          <p>Your incident data has not been changed. Retry the section or return to the incident overview.</p>
          <button type="button" onClick={() => this.setState({ error: null })}>Retry section</button>
        </section>
      );
    }
    return this.props.children;
  }
}
