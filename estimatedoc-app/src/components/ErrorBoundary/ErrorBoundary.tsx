import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import './ErrorBoundary.css';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorCount: number;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
      errorCount: 0
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error Boundary caught an error:', error, errorInfo);
    
    // Track error in analytics if available
    if (window.analytics?.trackError) {
      window.analytics.trackError({
        message: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack
      });
    }
    
    // Update state with error details
    this.setState(prevState => ({
      error,
      errorInfo,
      errorCount: prevState.errorCount + 1
    }));
    
    // Report to error tracking service in production
    if (process.env.NODE_ENV === 'production') {
      this.reportErrorToService(error, errorInfo);
    }
  }

  reportErrorToService = (error: Error, errorInfo: ErrorInfo) => {
    // Send error to monitoring service (e.g., Sentry, LogRocket)
    const errorData = {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href
    };
    
    // Send to analytics API
    fetch('/api/analytics/error', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(errorData)
    }).catch(err => {
      console.error('Failed to report error:', err);
    });
  };

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0
    });
  };

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback provided
      if (this.props.fallback) {
        return <>{this.props.fallback}</>;
      }

      // Default error UI
      return (
        <div className="error-boundary-container">
          <div className="error-boundary-content glass-modal">
            <div className="error-icon">
              <AlertTriangle size={48} />
            </div>
            
            <h1 className="error-title headline-medium">Something went wrong</h1>
            
            <p className="error-message body-large">
              We encountered an unexpected error. The issue has been logged and we'll look into it.
            </p>

            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="error-details">
                <summary className="label-medium">Error Details (Development Only)</summary>
                <div className="error-stack">
                  <p className="error-name label-small">
                    Error: {this.state.error.message}
                  </p>
                  <pre className="error-stacktrace body-small">
                    {this.state.error.stack}
                  </pre>
                  {this.state.errorInfo && (
                    <pre className="error-component-stack body-small">
                      {this.state.errorInfo.componentStack}
                    </pre>
                  )}
                </div>
              </details>
            )}

            <div className="error-actions">
              <button 
                className="button-primary"
                onClick={this.handleReset}
                aria-label="Try again"
              >
                <RefreshCw size={18} />
                Try Again
              </button>
              
              <button 
                className="button-secondary"
                onClick={this.handleReload}
                aria-label="Reload page"
              >
                <RefreshCw size={18} />
                Reload Page
              </button>
              
              <button 
                className="button-tertiary"
                onClick={this.handleGoHome}
                aria-label="Go to homepage"
              >
                <Home size={18} />
                Go to Home
              </button>
            </div>

            {this.state.errorCount > 2 && (
              <div className="error-persistent-warning">
                <p className="label-small">
                  This error keeps occurring. Please try refreshing the page or contact support if the issue persists.
                </p>
              </div>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Higher-order component for functional components
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  fallback?: ReactNode
): React.ComponentType<P> {
  return (props: P) => (
    <ErrorBoundary fallback={fallback}>
      <Component {...props} />
    </ErrorBoundary>
  );
}

// Custom hook for error handling in functional components
export function useErrorHandler() {
  return (error: Error) => {
    throw error; // This will be caught by the nearest ErrorBoundary
  };
}