// frontend/src/components/TelemetryErrorBoundary.jsx
/**
 * Enhanced Error Boundary with Telemetry Integration
 * Catches React component errors and reports them via telemetry
 */

import React from 'react';
import { telemetryService } from '../utils/telemetryService';

class TelemetryErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log error to telemetry service
    telemetryService.trackComponentError(error, errorInfo, this.props.componentName || 'Unknown');

    // Store error details in state
    this.setState({
      error,
      errorInfo
    });

    // Also log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('Error Boundary caught an error:', error, errorInfo);
    }
  }

  handleRetry = () => {
    // Track retry attempt
    telemetryService.track('error_boundary_retry', {
      componentName: this.props.componentName || 'Unknown',
      errorMessage: this.state.error?.message
    });

    // Reset error state
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default fallback UI with retry option
      return (
        <div style={{
          padding: '20px',
          border: '2px solid #ff6b6b',
          borderRadius: '8px',
          backgroundColor: '#fff5f5',
          color: '#c53030',
          fontFamily: 'system-ui, sans-serif'
        }}>
          <h2 style={{ margin: '0 0 10px 0', fontSize: '18px' }}>
            🚨 Component Error
          </h2>

          <p style={{ margin: '0 0 15px 0' }}>
            {this.props.componentName || 'A component'} encountered an error and couldn't render.
          </p>

          {process.env.NODE_ENV === 'development' && this.state.error && (
            <details style={{ margin: '10px 0', fontSize: '12px' }}>
              <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>
                Error Details (Development)
              </summary>
              <pre style={{
                backgroundColor: '#f7fafc',
                padding: '10px',
                borderRadius: '4px',
                overflow: 'auto',
                marginTop: '8px',
                whiteSpace: 'pre-wrap'
              }}>
                <strong>Error:</strong> {this.state.error.toString()}
                {this.state.errorInfo?.componentStack && (
                  <>
                    <br /><br />
                    <strong>Component Stack:</strong>
                    {this.state.errorInfo.componentStack}
                  </>
                )}
              </pre>
            </details>
          )}

          <div style={{ display: 'flex', gap: '10px', marginTop: '15px' }}>
            <button
              onClick={this.handleRetry}
              style={{
                padding: '8px 16px',
                backgroundColor: '#4299e1',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              🔄 Try Again
            </button>

            <button
              onClick={() => window.location.reload()}
              style={{
                padding: '8px 16px',
                backgroundColor: '#718096',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              🔃 Reload Page
            </button>
          </div>

          {this.props.showTelemetryInfo !== false && (
            <p style={{
              margin: '15px 0 0 0',
              fontSize: '12px',
              color: '#666',
              fontStyle: 'italic'
            }}>
              📊 Error details have been automatically reported for analysis
            </p>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

export default TelemetryErrorBoundary;
