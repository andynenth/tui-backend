import React from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, motion, shadows, layout, gradients } from '../../design-system/tokens.stylex';
import { animations } from '../../design-system/utils.stylex';
import LoadingOverlay from '../LoadingOverlay.stylex';
import ConnectionIndicator from '../ConnectionIndicator.stylex';

// Define waiting dots animation
const dotAnimation = stylex.keyframes({
  '0%, 60%, 100%': {
    transform: 'scale(1)',
    opacity: 0.5,
  },
  '30%': {
    transform: 'scale(1.3)',
    opacity: 1,
  },
});

// WaitingUI styles
const styles = stylex.create({
  container: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '1.5rem',
  },
  
  card: {
    borderRadius: '1rem',
    padding: '4rem',
    maxWidth: '28rem',
    width: '100%',
    textAlign: 'center',
    background: gradients.white,
    boxShadow: `'0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)', ${shadows.insetWhite}`,
  },
  
  connectionSection: {
    marginBottom: '3rem',
  },
  
  mainSection: {
    marginBottom: '4rem',
  },
  
  phaseIcon: {
    fontSize: '4rem',
    marginBottom: '1.5rem',
    lineHeight: 1,
  },
  
  phaseTitle: {
    fontSize: '1.5rem',
    fontWeight: '700',
    marginBottom: '0.5rem',
    color: '#495057',
  },
  
  message: {
    fontSize: '1.125rem',
    color: '#adb5bd',
  },
  
  loadingSection: {
    marginBottom: '3rem',
  },
  
  errorSection: {
    marginBottom: '3rem',
    padding: '1.5rem',
    borderRadius: '0.5rem',
    backgroundColor: 'rgba(220, 53, 69, 0.1)',
    border: '1px solid rgba(220, 53, 69, 0.3)',
  },
  
  errorText: {
    fontSize: '0.875rem',
    marginBottom: '1rem',
    color: '#dc3545',
  },
  
  retryButton: {
    padding: `'0.5rem' '1.5rem'`,
    borderRadius: '0.5rem',
    fontSize: '0.875rem',
    fontWeight: '500',
    transition: `colors '300ms' 'cubic-bezier(0.4, 0, 0.2, 1)'`,
    color: '#ffffff',
    background: gradients.danger,
    border: 'none',
    cursor: 'pointer',
    
    ':hover': {
      backgroundColor: '#a71e2a',
    },
  },
  
  waitingDots: {
    display: 'flex',
    justifyContent: 'center',
    gap: '0.5rem',
    marginBottom: '3rem',
  },
  
  waitingDot: {
    width: '12px',
    height: '12px',
    borderRadius: '9999px',
    backgroundColor: '#0d6efd',
    animation: `${dotAnimation} 1.4s infinite`,
  },
  
  dot1: {
    animationDelay: '0s',
  },
  
  dot2: {
    animationDelay: '0.2s',
  },
  
  dot3: {
    animationDelay: '0.4s',
  },
  
  phaseInfo: {
    fontSize: '0.875rem',
    color: '#6c757d',
    display: 'flex',
    flexDirection: 'column',
    gap: '0.25rem',
  },
  
  phaseInfoRow: {
    display: 'flex',
    justifyContent: 'center',
    gap: '0.25rem',
  },
  
  phaseInfoLabel: {
    color: '#6c757d',
  },
  
  phaseInfoValue: {
    fontWeight: '500',
    color: '#adb5bd',
  },
  
  cancelSection: {
    marginTop: '3rem',
  },
  
  cancelButton: {
    fontSize: '0.875rem',
    textDecoration: 'underline',
    transition: `color '300ms' 'cubic-bezier(0.4, 0, 0.2, 1)'`,
    color: '#ced4da',
    backgroundColor: 'none',
    border: 'none',
    cursor: 'pointer',
    
    ':hover': {
      color: '#6c757d',
    },
  },
});

// Helper functions
function getPhaseIcon(phase) {
  switch (phase) {
    case 'waiting':
      return '⏳';
    case 'preparation':
      return '🃏';
    case 'declaration':
      return '🎯';
    case 'turn':
      return '🎮';
    case 'scoring':
      return '🏆';
    default:
      return '⏳';
  }
}

function getPhaseTitle(phase) {
  switch (phase) {
    case 'waiting':
      return 'Waiting for Game';
    case 'preparation':
      return 'Preparing Cards';
    case 'declaration':
      return 'Making Declarations';
    case 'turn':
      return 'Playing Turn';
    case 'scoring':
      return 'Calculating Scores';
    default:
      return 'Waiting';
  }
}

function getConnectionStatus(isConnected, isConnecting, isReconnecting, error) {
  if (error) return 'Error';
  if (isReconnecting) return 'Reconnecting';
  if (isConnecting) return 'Connecting';
  if (isConnected) return 'Connected';
  return 'Disconnected';
}

export function WaitingUI({
  // Connection props
  isConnected,
  isConnecting,
  isReconnecting,
  connectionError,

  // Status props
  message = 'Waiting...',
  phase = 'waiting',

  // Action props
  onRetry,
  onCancel,
}) {
  return (
    <div {...stylex.props(styles.container)}>
      <div {...stylex.props(styles.card)}>
        {/* Connection Status */}
        <div {...stylex.props(styles.connectionSection)}>
          <ConnectionIndicator
            isConnected={isConnected}
            isConnecting={isConnecting}
            isReconnecting={isReconnecting}
            error={connectionError}
          />
        </div>

        {/* Main Status */}
        <div {...stylex.props(styles.mainSection)}>
          <div {...stylex.props(styles.phaseIcon)}>{getPhaseIcon(phase)}</div>

          <h1 {...stylex.props(styles.phaseTitle)}>
            {getPhaseTitle(phase)}
          </h1>

          <p {...stylex.props(styles.message)}>
            {message}
          </p>
        </div>

        {/* Loading Animation */}
        {(isConnecting || isReconnecting) && (
          <div {...stylex.props(styles.loadingSection)}>
            <LoadingOverlay
              isVisible={true}
              message={isReconnecting ? 'Reconnecting...' : 'Connecting...'}
              overlay={false}
            />
          </div>
        )}

        {/* Error State */}
        {connectionError && (
          <div {...stylex.props(styles.errorSection)}>
            <div {...stylex.props(styles.errorText)}>
              Connection Error: {connectionError}
            </div>

            {onRetry && (
              <button
                {...stylex.props(styles.retryButton)}
                onClick={onRetry}
                aria-label="Retry connection"
              >
                Retry Connection
              </button>
            )}
          </div>
        )}

        {/* Waiting Animation */}
        {!connectionError && !isConnecting && !isReconnecting && (
          <div {...stylex.props(styles.waitingDots)}>
            <div {...stylex.props(styles.waitingDot, styles.dot1)} />
            <div {...stylex.props(styles.waitingDot, styles.dot2)} />
            <div {...stylex.props(styles.waitingDot, styles.dot3)} />
          </div>
        )}

        {/* Phase Information */}
        <div {...stylex.props(styles.phaseInfo)}>
          <div {...stylex.props(styles.phaseInfoRow)}>
            <span {...stylex.props(styles.phaseInfoLabel)}>Phase:</span>
            <span {...stylex.props(styles.phaseInfoValue)}>{phase}</span>
          </div>
          <div {...stylex.props(styles.phaseInfoRow)}>
            <span {...stylex.props(styles.phaseInfoLabel)}>Status:</span>
            <span {...stylex.props(styles.phaseInfoValue)}>
              {getConnectionStatus(
                isConnected,
                isConnecting,
                isReconnecting,
                connectionError
              )}
            </span>
          </div>
        </div>

        {/* Cancel Button */}
        {onCancel && (
          <div {...stylex.props(styles.cancelSection)}>
            <button
              {...stylex.props(styles.cancelButton)}
              onClick={onCancel}
              aria-label="Cancel and return"
            >
              Cancel
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// PropTypes definition
WaitingUI.propTypes = {
  // Connection props
  isConnected: PropTypes.bool.isRequired,
  isConnecting: PropTypes.bool,
  isReconnecting: PropTypes.bool,
  connectionError: PropTypes.string,

  // Status props
  message: PropTypes.string,
  phase: PropTypes.oneOf([
    'waiting',
    'preparation',
    'declaration',
    'turn',
    'scoring',
  ]),

  // Action props
  onRetry: PropTypes.func,
  onCancel: PropTypes.func,
};

WaitingUI.defaultProps = {
  isConnecting: false,
  isReconnecting: false,
  connectionError: null,
  message: 'Waiting...',
  phase: 'waiting',
  onRetry: null,
  onCancel: null,
};

export default WaitingUI;