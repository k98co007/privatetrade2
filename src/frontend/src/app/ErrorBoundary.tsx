import React from 'react';

type ErrorBoundaryState = {
  hasError: boolean;
  message: string;
};

export class ErrorBoundary extends React.Component<React.PropsWithChildren, ErrorBoundaryState> {
  constructor(props: React.PropsWithChildren) {
    super(props);
    this.state = { hasError: false, message: '' };
  }

  static getDerivedStateFromError(error: unknown): ErrorBoundaryState {
    return {
      hasError: true,
      message: error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다.',
    };
  }

  override render() {
    if (this.state.hasError) {
      return (
        <main style={{ padding: 16 }}>
          <h1>오류가 발생했습니다</h1>
          <p>{this.state.message}</p>
        </main>
      );
    }

    return this.props.children;
  }
}
