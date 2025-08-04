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
    padding: spacing.lg,
  },
  
  card: {
    borderRadius: layout.radiusXl,
    padding: spacing.xxxl,
    maxWidth: '28rem',
    width: '100%',
    textAlign: 'center',
    background: gradients.white,
    boxShadow: `${shadows.lg}, ${shadows.insetWhite}`,
  },
  
  connectionSection: {
    marginBottom: spacing.xxl,
  },
  
  mainSection: {
    marginBottom: spacing.xxxl,
  },
  
  phaseIcon: {
    fontSize: '4rem',
    marginBottom: spacing.lg,
    lineHeight: 1,
  },
  
  phaseTitle: {
    fontSize: typography.text2xl,
    fontWeight: typography.weightBold,
    marginBottom: spacing.sm,
    color: colors.gray700,
  },
  
  message: {
    fontSize: typography.textLg,
    color: colors.gray500,
  },
  
  loadingSection: {
    marginBottom: spacing.xxl,
  },
  
  errorSection: {
    marginBottom: spacing.xxl,
    padding: spacing.lg,
    borderRadius: layout.radiusLg,
    backgroundColor: 'rgba(220, 53, 69, 0.1)',
    border: '1px solid rgba(220, 53, 69, 0.3)',
  },
  
  errorText: {
    fontSize: typography.textSm,
    marginBottom: spacing.md,
    color: colors.danger,
  },
  
  retryButton: {
    padding: `${spacing.sm} ${spacing.lg}`,
    borderRadius: layout.radiusLg,
    fontSize: typography.textSm,
    fontWeight: typography.weightMedium,
    transition: `colors ${motion.durationBase} ${motion.easeInOut}`,
    color: colors.white,
    background: gradients.danger,
    border: 'none',
    cursor: 'pointer',
    
    ':hover': {
      backgroundColor: colors.dangerDark,
    },
  },
  
  waitingDots: {
    display: 'flex',
    justifyContent: 'center',
    gap: spacing.sm,
    marginBottom: spacing.xxl,
  },
  
  waitingDot: {
    width: '12px',
    height: '12px',
    borderRadius: layout.radiusFull,
    backgroundColor: colors.primary,
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
    fontSize: typography.textSm,
    color: colors.gray600,
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.xs,
  },
  
  phaseInfoRow: {
    display: 'flex',
    justifyContent: 'center',
    gap: spacing.xs,
  },
  
  phaseInfoLabel: {
    color: colors.gray600,
  },
  
  phaseInfoValue: {
    fontWeight: typography.weightMedium,
    color: colors.gray500,
  },
  
  cancelSection: {
    marginTop: spacing.xxl,
  },
  
  cancelButton: {
    fontSize: typography.textSm,
    textDecoration: 'underline',
    transition: `color ${motion.durationBase} ${motion.easeInOut}`,
    color: colors.gray400,
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    
    ':hover': {
      color: colors.gray600,
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