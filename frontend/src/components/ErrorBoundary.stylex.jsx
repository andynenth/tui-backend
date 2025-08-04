import React from 'react';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, motion, shadows, layout } from '../design-system/tokens.stylex';

// ErrorBoundary styles
const styles = stylex.create({
  container: {
    minHeight: '100vh',
    backgroundColor: colors.gray100,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.lg,
  },
  
  card: {
    backgroundColor: colors.white,
    borderRadius: layout.radiusLg,
    boxShadow: shadows.lg,
    padding: spacing.xxl,
    maxWidth: '28rem',
    width: '100%',
  },
  
  errorSection: {
    textAlign: 'center',
    marginBottom: spacing.lg,
  },
  
  errorIcon: {
    width: '64px',
    height: '64px',
    margin: '0 auto',
    marginBottom: spacing.lg,
    color: colors.danger,
  },
  
  errorTitle: {
    fontSize: typography.textXl,
    fontWeight: typography.weightBold,
    marginBottom: spacing.sm,
    color: colors.danger,
  },
  
  errorMessage: {
    color: colors.gray600,
    marginBottom: spacing.lg,
  },
  
  buttonGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.sm,
  },
  
  button: {
    width: '100%',
    padding: `${spacing.sm} ${spacing.lg}`,
    borderRadius: layout.radiusMd,
    border: 'none',
    cursor: 'pointer',
    fontSize: typography.textBase,
    fontWeight: typography.weightMedium,
    transition: `all ${motion.durationBase} ${motion.easeInOut}`,
  },
  
  primaryButton: {
    backgroundColor: colors.primary,
    color: colors.white,
    
    ':hover': {
      backgroundColor: colors.primaryDark,
    },
  },
  
  secondaryButton: {
    backgroundColor: colors.gray300,
    color: colors.gray700,
    
    ':hover': {
      backgroundColor: colors.gray400,
    },
  },
  
  errorDetails: {
    marginTop: spacing.lg,
    padding: spacing.sm,
    backgroundColor: colors.gray100,
    borderRadius: layout.radiusMd,
    fontSize: typography.textXs,
  },
  
  errorSummary: {
    cursor: 'pointer',
    fontWeight: typography.weightMedium,
  },
  
  errorStack: {
    marginTop: spacing.sm,
    whiteSpace: 'pre-wrap',
    color: colors.danger,
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