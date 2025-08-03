/**
 * 🎮 **WaitingUI Component** - Pure Waiting State Interface with StyleX
 *
 * Phase 2, Task 2.2: Pure UI Components
 *
 * Features:
 * ✅ Pure functional component (props in, JSX out)
 * ✅ No hooks except local UI state
 * ✅ Comprehensive prop interfaces
 * ✅ Accessible and semantic HTML
 * ✅ StyleX for type-safe, optimized styling
 */

import React from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
import LoadingOverlay from '../LoadingOverlay.stylex';
import ConnectionIndicator from '../ConnectionIndicator';
import Button from '../Button.stylex';
import { colors, spacing, shadows, layout, motion, typography } from '../../design-system/tokens.stylex';

// Animation keyframes
const fadeIn = stylex.keyframes({
  '0%': {
    opacity: 0,
    transform: 'translateY(20px)',
  },
  '100%': {
    opacity: 1,
    transform: 'translateY(0)',
  },
});

const pulse = stylex.keyframes({
  '0%, 100%': {
    opacity: 1,
  },
  '50%': {
    opacity: 0.5,
  },
});

const bounce = stylex.keyframes({
  '0%, 100%': {
    transform: 'translateY(0)',
  },
  '50%': {
    transform: 'translateY(-10px)',
  },
});

const styles = stylex.create({
  container: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.md,
    backgroundColor: colors.background,
  },
  
  card: {
    borderRadius: layout.radiusXl,
    padding: spacing.xxl,
    maxWidth: '28rem',
    width: '100%',
    textAlign: 'center',
    backgroundColor: colors.surface,
    backgroundImage: colors.backgroundGradient,
    boxShadow: `${shadows.lg}, ${shadows.insetWhite}`,
    animation: `${fadeIn} ${motion.durationNormal} ${motion.easeOut}`,
  },
  
  connectionSection: {
    marginBottom: spacing.xl,
  },
  
  mainSection: {
    marginBottom: spacing.xxl,
  },
  
  phaseIcon: {
    fontSize: '4rem',
    marginBottom: spacing.md,
    animation: `${bounce} 2s ${motion.easeInOut} infinite`,
  },
  
  phaseTitle: {
    fontSize: typography.textXxl,
    fontWeight: typography.weightBold,
    color: colors.gray700,
    marginBottom: spacing.sm,
  },
  
  statusMessage: {
    fontSize: typography.textLg,
    color: colors.gray500,
  },
  
  loadingSection: {
    marginBottom: spacing.xl,
  },
  
  errorSection: {
    marginBottom: spacing.xl,
    padding: spacing.md,
    borderRadius: layout.radiusMd,
    backgroundColor: 'rgba(220, 53, 69, 0.1)',
    border: '1px solid rgba(220, 53, 69, 0.3)',
  },
  
  errorText: {
    fontSize: typography.textSm,
    color: colors.danger,
    marginBottom: spacing.md,
  },
  
  // Waiting dots animation
  waitingDots: {
    display: 'flex',
    justifyContent: 'center',
    gap: spacing.sm,
    marginBottom: spacing.xl,
  },
  
  waitingDot: {
    width: '12px',
    height: '12px',
    borderRadius: layout.radiusFull,
    backgroundColor: colors.primary,
    animation: `${pulse} 1.4s ${motion.easeInOut} infinite`,
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
  
  // Phase information
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
  
  phaseLabel: {
    color: colors.gray600,
  },
  
  phaseValue: {
    fontWeight: typography.weightMedium,
    color: colors.gray500,
  },
  
  // Cancel button section
  cancelSection: {
    marginTop: spacing.xl,
  },
  
  cancelButton: {
    fontSize: typography.textSm,
    color: colors.gray400,
    textDecoration: 'underline',
    backgroundColor: 'transparent',
    border: 'none',
    cursor: 'pointer',
    padding: spacing.xs,
    transition: motion.transitionBase,
    
    ':hover': {
      color: colors.gray600,
    },
  },
  
  // Phase-specific colors
  phaseWaiting: {
    color: colors.warning,
  },
  
  phasePreparation: {
    color: colors.primary,
  },
  
  phaseDeclaration: {
    color: colors.secondary,
  },
  
  phaseTurn: {
    color: colors.success,
  },
  
  phaseScoring: {
    color: colors.warning,
  },
});

/**
 * Pure UI component for waiting states
 */
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
  
  // Additional props
  className = '',
}) {
  // Get phase-specific icon color
  const getPhaseIconStyle = () => {
    const phaseStyles = {
      waiting: styles.phaseWaiting,
      preparation: styles.phasePreparation,
      declaration: styles.phaseDeclaration,
      turn: styles.phaseTurn,
      scoring: styles.phaseScoring,
    };
    return phaseStyles[phase] || styles.phaseWaiting;
  };
  
  return (
    <div {...stylex.props(styles.container, className && { className })}>
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
          <div {...stylex.props(styles.phaseIcon, getPhaseIconStyle())}>
            {getPhaseIcon(phase)}
          </div>
          
          <h1 {...stylex.props(styles.phaseTitle)}>
            {getPhaseTitle(phase)}
          </h1>
          
          <p {...stylex.props(styles.statusMessage)}>
            {message}
          </p>
        </div>
        
        {/* Loading Animation */}
        {(isConnecting || isReconnecting) && (
          <div {...stylex.props(styles.loadingSection)}>
            <LoadingOverlay
              isVisible={true}
              message={isReconnecting ? 'Reconnecting...' : 'Connecting...'}
              subtitle="Please wait"
              overlay={false}
              size="small"
              spinnerType="dual"
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
              <Button
                onClick={onRetry}
                variant="danger"
                size="small"
                aria-label="Retry connection"
              >
                Retry Connection
              </Button>
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
            <span {...stylex.props(styles.phaseLabel)}>Phase:</span>
            <span {...stylex.props(styles.phaseValue)}>{phase}</span>
          </div>
          <div {...stylex.props(styles.phaseInfoRow)}>
            <span {...stylex.props(styles.phaseLabel)}>Status:</span>
            <span {...stylex.props(styles.phaseValue)}>
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
  
  // Additional props
  className: PropTypes.string,
};

WaitingUI.defaultProps = {
  isConnecting: false,
  isReconnecting: false,
  connectionError: null,
  message: 'Waiting...',
  phase: 'waiting',
  onRetry: null,
  onCancel: null,
  className: '',
};

export default WaitingUI;