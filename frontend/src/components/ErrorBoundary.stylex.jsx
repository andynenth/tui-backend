/**
 * 🛡️ **ErrorBoundary Component** - Error Handling with StyleX
 *
 * Features:
 * ✅ Graceful error catching and display
 * ✅ Development mode error details
 * ✅ Retry and refresh functionality
 * ✅ Styled error UI with animations
 * ✅ StyleX for optimized styling
 */

import React from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, shadows, layout, motion, typography } from '../design-system/tokens.stylex';

// Animation keyframes
const fadeIn = stylex.keyframes({
  '0%': {
    opacity: 0,
    transform: 'scale(0.95)',
  },
  '100%': {
    opacity: 1,
    transform: 'scale(1)',
  },
});

const shake = stylex.keyframes({
  '0%, 100%': {
    transform: 'translateX(0)',
  },
  '10%, 30%, 50%, 70%, 90%': {
    transform: 'translateX(-2px)',
  },
  '20%, 40%, 60%, 80%': {
    transform: 'translateX(2px)',
  },
});

const rotate = stylex.keyframes({
  '0%': {
    transform: 'rotate(0deg)',
  },
  '100%': {
    transform: 'rotate(360deg)',
  },
});

const styles = stylex.create({
  // Container styles
  container: {
    minHeight: '100vh',
    backgroundColor: colors.gray100,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.lg,
  },
  
  // Error card
  card: {
    backgroundColor: colors.surface,
    borderRadius: layout.radiusLg,
    boxShadow: shadows.lg,
    padding: spacing.xl,
    maxWidth: '28rem',
    width: '100%',
    animation: `${fadeIn} ${motion.durationNormal} ${motion.easeOut}`,
  },
  
  // Error icon container
  iconContainer: {
    textAlign: 'center',
    color: colors.danger,
    marginBottom: spacing.lg,
  },
  
  errorIcon: {
    width: '4rem',
    height: '4rem',
    margin: '0 auto',
    marginBottom: spacing.lg,
    animation: `${shake} 0.5s ${motion.easeOut}`,
  },
  
  // Text styles
  title: {
    fontSize: typography.headingMd,
    fontWeight: typography.weightBold,
    marginBottom: spacing.sm,
    color: colors.textDark,
  },
  
  message: {
    fontSize: typography.textMd,
    color: colors.gray600,
    marginBottom: spacing.lg,
    lineHeight: 1.5,
  },
  
  // Button container
  buttonContainer: {
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.sm,
  },
  
  // Button base styles
  button: {
    width: '100%',
    padding: `${spacing.sm} ${spacing.lg}`,
    borderRadius: layout.radiusMd,
    fontSize: typography.textMd,
    fontWeight: typography.weightMedium,
    border: 'none',
    cursor: 'pointer',
    transition: motion.transitionBase,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
  },
  
  // Primary button
  primaryButton: {
    backgroundColor: colors.primary,
    color: colors.textLight,
    
    ':hover': {
      backgroundColor: colors.primaryHover,
      transform: 'translateY(-1px)',
      boxShadow: shadows.md,
    },
    
    ':active': {
      transform: 'translateY(0)',
    },
  },
  
  // Secondary button
  secondaryButton: {
    backgroundColor: colors.gray300,
    color: colors.gray700,
    
    ':hover': {
      backgroundColor: colors.gray400,
      transform: 'translateY(-1px)',
      boxShadow: shadows.sm,
    },
    
    ':active': {
      transform: 'translateY(0)',
    },
  },
  
  // Loading state
  buttonLoading: {
    opacity: 0.7,
    cursor: 'not-allowed',
  },
  
  loadingIcon: {
    animation: `${rotate} 1s linear infinite`,
  },
  
  // Error details (dev only)
  details: {
    marginTop: spacing.lg,
    padding: spacing.sm,
    backgroundColor: colors.gray100,
    borderRadius: layout.radiusMd,
    fontSize: typography.textXs,
  },
  
  detailsSummary: {
    cursor: 'pointer',
    fontWeight: typography.weightMedium,
    padding: spacing.xs,
    userSelect: 'none',
    
    ':hover': {
      backgroundColor: colors.gray200,
      borderRadius: layout.radiusSm,
    },
  },
  
  detailsContent: {
    marginTop: spacing.sm,
    padding: spacing.sm,
    whiteSpace: 'pre-wrap',
    color: colors.danger,
    fontFamily: 'monospace',
    fontSize: '0.7rem',
    lineHeight: 1.4,
    overflowX: 'auto',
    backgroundColor: colors.surface,
    borderRadius: layout.radiusSm,
    border: `1px solid ${colors.danger}`,
  },
  
  // Alternative minimal error state
  minimalError: {
    padding: spacing.lg,
    backgroundColor: colors.dangerLight,
    color: colors.danger,
    borderRadius: layout.radiusMd,
    textAlign: 'center',
    margin: spacing.lg,
    boxShadow: shadows.sm,
  },
});

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null, 
      errorInfo: null,
      isRetrying: false,
    };
  }

  static getDerivedStateFromError(_error) {
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

    // Call optional error handler
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  handleRefresh = () => {
    this.setState({ isRetrying: true });
    setTimeout(() => {
      window.location.reload();
    }, 500);
  };

  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      isRetrying: false,
    });
  };

  render() {
    const { hasError, error, errorInfo, isRetrying } = this.state;
    const { fallback, minimal } = this.props;

    if (hasError) {
      // Use custom fallback if provided
      if (fallback) {
        return fallback(error, errorInfo, this.handleRetry);
      }

      // Minimal error display
      if (minimal) {
        return (
          <div {...stylex.props(styles.minimalError)}>
            <div>⚠️ Something went wrong</div>
            <button 
              onClick={this.handleRetry}
              style={{ marginTop: '8px', textDecoration: 'underline', background: 'none', border: 'none', cursor: 'pointer' }}
            >
              Try again
            </button>
          </div>
        );
      }

      // Full error display
      return (
        <div {...stylex.props(styles.container)}>
          <div {...stylex.props(styles.card)}>
            <div {...stylex.props(styles.iconContainer)}>
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
              <h2 {...stylex.props(styles.title)}>Something went wrong</h2>
              <p {...stylex.props(styles.message)}>
                An unexpected error occurred. Please try refreshing the page or clicking try again.
              </p>
            </div>

            <div {...stylex.props(styles.buttonContainer)}>
              <button
                onClick={this.handleRefresh}
                disabled={isRetrying}
                {...stylex.props(
                  styles.button,
                  styles.primaryButton,
                  isRetrying && styles.buttonLoading
                )}
              >
                {isRetrying ? (
                  <>
                    <span {...stylex.props(styles.loadingIcon)}>⟳</span>
                    Refreshing...
                  </>
                ) : (
                  <>
                    <span>↻</span>
                    Refresh Page
                  </>
                )}
              </button>

              <button
                onClick={this.handleRetry}
                disabled={isRetrying}
                {...stylex.props(
                  styles.button,
                  styles.secondaryButton,
                  isRetrying && styles.buttonLoading
                )}
              >
                Try Again
              </button>
            </div>

            {process.env.NODE_ENV === 'development' && error && (
              <details {...stylex.props(styles.details)}>
                <summary {...stylex.props(styles.detailsSummary)}>
                  🔍 Error Details (Development Only)
                </summary>
                <pre {...stylex.props(styles.detailsContent)}>
                  {error.toString()}
                  {errorInfo?.componentStack}
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

ErrorBoundary.propTypes = {
  children: PropTypes.node.isRequired,
  fallback: PropTypes.func,
  onError: PropTypes.func,
  minimal: PropTypes.bool,
};

ErrorBoundary.defaultProps = {
  fallback: null,
  onError: null,
  minimal: false,
};

export default ErrorBoundary;