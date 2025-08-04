import React from 'react';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, motion, shadows, layout } from '../design-system/tokens.stylex';

// ErrorBoundary styles
const styles = stylex.create({
  container: {
    minHeight: '100vh',
    backgroundColor: '#f1f3f5',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '1.5rem',
  },
  
  card: {
    backgroundColor: '#ffffff',
    borderRadius: '0.5rem',
    boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    padding: '3rem',
    maxWidth: '28rem',
    width: '100%',
  },
  
  errorSection: {
    textAlign: 'center',
    marginBottom: '1.5rem',
  },
  
  errorIcon: {
    width: '64px',
    height: '64px',
    margin: '0 auto',
    marginBottom: '1.5rem',
    color: '#dc3545',
  },
  
  errorTitle: {
    fontSize: '1.25rem',
    fontWeight: '700',
    marginBottom: '0.5rem',
    color: '#dc3545',
  },
  
  errorMessage: {
    color: '#6c757d',
    marginBottom: '1.5rem',
  },
  
  buttonGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
  },
  
  button: {
    width: '100%',
    padding: `'0.5rem' '1.5rem'`,
    borderRadius: '0.375rem',
    border: 'none',
    cursor: 'pointer',
    fontSize: '1rem',
    fontWeight: '500',
    transition: `all '300ms' 'cubic-bezier(0.4, 0, 0.2, 1)'`,
  },
  
  primaryButton: {
    backgroundColor: '#0d6efd',
    color: '#ffffff',
    
    ':hover': {
      backgroundColor: '#0056b3',
    },
  },
  
  secondaryButton: {
    backgroundColor: '#dee2e6',
    color: '#495057',
    
    ':hover': {
      backgroundColor: '#ced4da',
    },
  },
  
  errorDetails: {
    marginTop: '1.5rem',
    padding: '0.5rem',
    backgroundColor: '#f1f3f5',
    borderRadius: '0.375rem',
    fontSize: '0.75rem',
  },
  
  errorSummary: {
    cursor: 'pointer',
    fontWeight: '500',
  },
  
  errorStack: {
    marginTop: '0.5rem',
    whiteSpace: 'pre-wrap',
    color: '#dc3545',
    fontFamily: typography.fontMono || 'monospace',
  },
});

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({
      error,
      errorInfo,
    });

    // Log error to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('Error caught by boundary:', error, errorInfo);
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div {...stylex.props(styles.container)}>
          <div {...stylex.props(styles.card)}>
            <div {...stylex.props(styles.errorSection)}>
              <svg
                {...stylex.props(styles.errorIcon)}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 18.5c-.77.833.192 2.5 1.732 2.5z"
                />
              </svg>
              <h2 {...stylex.props(styles.errorTitle)}>Something went wrong</h2>
              <p {...stylex.props(styles.errorMessage)}>
                An unexpected error occurred. Please try refreshing the page.
              </p>
            </div>

            <div {...stylex.props(styles.buttonGroup)}>
              <button
                onClick={() => window.location.reload()}
                {...stylex.props(styles.button, styles.primaryButton)}
              >
                Refresh Page
              </button>

              <button
                onClick={() =>
                  this.setState({
                    hasError: false,
                    error: null,
                    errorInfo: null,
                  })
                }
                {...stylex.props(styles.button, styles.secondaryButton)}
              >
                Try Again
              </button>
            </div>

            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details {...stylex.props(styles.errorDetails)}>
                <summary {...stylex.props(styles.errorSummary)}>
                  Error Details
                </summary>
                <pre {...stylex.props(styles.errorStack)}>
                  {this.state.error.toString()}
                  {this.state.errorInfo.componentStack}
                </pre>
              </details>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;