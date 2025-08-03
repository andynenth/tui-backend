/**
 * 🔌 **ConnectionIndicator Component** - Connection Status Display with StyleX
 *
 * Features:
 * ✅ Real-time connection status
 * ✅ Visual status indicators with animations
 * ✅ Error state display
 * ✅ Disconnected players tracking
 * ✅ StyleX for optimized styling
 */

import React from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, shadows, layout, motion, typography } from '../design-system/tokens.stylex';

// Animation keyframes
const pulse = stylex.keyframes({
  '0%, 100%': {
    opacity: 1,
  },
  '50%': {
    opacity: 0.5,
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

const fadeIn = stylex.keyframes({
  '0%': {
    opacity: 0,
    transform: 'translateY(-10px)',
  },
  '100%': {
    opacity: 1,
    transform: 'translateY(0)',
  },
});

const styles = stylex.create({
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.sm,
    animation: `${fadeIn} ${motion.durationFast} ${motion.easeOut}`,
  },
  
  // Status indicator base
  indicator: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: spacing.sm,
    padding: `${spacing.xs} ${spacing.md}`,
    borderRadius: layout.radiusFull,
    fontSize: typography.textSm,
    fontWeight: typography.weightMedium,
    color: colors.textLight,
    transition: motion.transitionBase,
    boxShadow: shadows.sm,
  },
  
  // Status variants
  statusConnected: {
    backgroundColor: colors.success,
  },
  
  statusConnecting: {
    backgroundColor: colors.warning,
    animation: `${pulse} 1.5s ${motion.easeInOut} infinite`,
  },
  
  statusReconnecting: {
    backgroundColor: colors.warning,
    animation: `${pulse} 1s ${motion.easeInOut} infinite`,
  },
  
  statusDisconnected: {
    backgroundColor: colors.gray500,
  },
  
  statusError: {
    backgroundColor: colors.danger,
  },
  
  // Icon styles
  icon: {
    fontSize: typography.textXs,
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  
  iconAnimated: {
    animation: `${rotate} 1s linear infinite`,
  },
  
  // Text styles
  statusText: {
    letterSpacing: '0.025em',
  },
  
  details: {
    fontSize: typography.textXs,
    opacity: 0.75,
    marginLeft: spacing.xs,
  },
  
  errorIcon: {
    fontSize: typography.textXs,
    opacity: 0.75,
    cursor: 'help',
  },
  
  // Disconnected players banner
  disconnectedBanner: {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.xs,
    padding: `${spacing.xs} ${spacing.md}`,
    backgroundColor: colors.warningLight,
    color: colors.gray700,
    borderRadius: layout.radiusFull,
    fontSize: typography.textXs,
    boxShadow: shadows.sm,
    animation: `${fadeIn} ${motion.durationNormal} ${motion.easeOut}`,
    animationDelay: '0.1s',
    animationFillMode: 'backwards',
  },
  
  disconnectedIcon: {
    fontSize: typography.textSm,
  },
  
  disconnectedText: {
    flex: 1,
  },
  
  // Minimal mode
  minimal: {
    padding: `${spacing.xs} ${spacing.sm}`,
    fontSize: typography.textXs,
  },
  
  // Inline mode
  inline: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  
  // Floating mode
  floating: {
    position: 'fixed',
    top: spacing.lg,
    right: spacing.lg,
    zIndex: layout.zModal,
  },
});

/**
 * ConnectionIndicator - Visual connection status display
 */
export function ConnectionIndicator({
  isConnected = false,
  isConnecting = false,
  isReconnecting = false,
  error = null,
  roomId = null,
  showDetails = false,
  className = '',
  disconnectedPlayers = [],
  variant = 'default', // default, minimal, inline, floating
}) {
  const getStatusInfo = () => {
    if (error) {
      return {
        status: 'error',
        text: 'Connection Error',
        style: styles.statusError,
        icon: '❌',
        animated: false,
      };
    }

    if (isReconnecting) {
      return {
        status: 'reconnecting',
        text: 'Reconnecting...',
        style: styles.statusReconnecting,
        icon: '🔄',
        animated: true,
      };
    }

    if (isConnecting) {
      return {
        status: 'connecting',
        text: 'Connecting...',
        style: styles.statusConnecting,
        icon: '⚡',
        animated: false,
      };
    }

    if (isConnected) {
      return {
        status: 'connected',
        text: 'Connected',
        style: styles.statusConnected,
        icon: '✅',
        animated: false,
      };
    }

    return {
      status: 'disconnected',
      text: 'Disconnected',
      style: styles.statusDisconnected,
      icon: '⚫',
      animated: false,
    };
  };

  const statusInfo = getStatusInfo();
  const hasDisconnectedPlayers = disconnectedPlayers.length > 0;

  // Get variant styles
  const variantStyles = {
    minimal: styles.minimal,
    inline: styles.inline,
    floating: styles.floating,
  }[variant];

  const containerStyles = {
    inline: styles.inline,
    floating: styles.floating,
  }[variant];

  return (
    <div {...stylex.props(
      styles.container,
      containerStyles,
      className && { className }
    )}>
      <div {...stylex.props(
        styles.indicator,
        statusInfo.style,
        variantStyles
      )}>
        <span {...stylex.props(
          styles.icon,
          statusInfo.animated && styles.iconAnimated
        )}>
          {statusInfo.icon}
        </span>
        
        <span {...stylex.props(styles.statusText)}>
          {statusInfo.text}
        </span>

        {showDetails && roomId && (
          <span {...stylex.props(styles.details)}>
            ({roomId})
          </span>
        )}

        {error && showDetails && (
          <span 
            {...stylex.props(styles.errorIcon)}
            title={error.message || error}
          >
            ⚠️
          </span>
        )}
      </div>

      {hasDisconnectedPlayers && variant !== 'minimal' && (
        <div {...stylex.props(styles.disconnectedBanner)}>
          <span {...stylex.props(styles.disconnectedIcon)}>🤖</span>
          <span {...stylex.props(styles.disconnectedText)}>
            AI Playing for: {disconnectedPlayers.join(', ')} - Can reconnect anytime
          </span>
        </div>
      )}
    </div>
  );
}

ConnectionIndicator.propTypes = {
  isConnected: PropTypes.bool,
  isConnecting: PropTypes.bool,
  isReconnecting: PropTypes.bool,
  error: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.object,
  ]),
  roomId: PropTypes.string,
  showDetails: PropTypes.bool,
  className: PropTypes.string,
  disconnectedPlayers: PropTypes.arrayOf(PropTypes.string),
  variant: PropTypes.oneOf(['default', 'minimal', 'inline', 'floating']),
};

export default ConnectionIndicator;