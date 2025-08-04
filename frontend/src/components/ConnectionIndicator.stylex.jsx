import React from 'react';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, motion, layout } from '../design-system/tokens.stylex';
import { animations } from '../design-system/utils.stylex';

// Connection indicator styles
const styles = stylex.create({
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.sm,
  },
  
  indicator: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: spacing.sm,
    paddingTop: spacing.xs,
    paddingBottom: spacing.xs,
    paddingLeft: spacing.md,
    paddingRight: spacing.md,
    borderRadius: layout.radiusFull,
    fontSize: typography.textSm,
    fontWeight: typography.weightMedium,
    color: colors.white,
    transition: `all ${motion.durationBase} ${motion.easeInOut}`,
  },
  
  // Status variants
  connected: {
    backgroundColor: colors.success,
  },
  
  connecting: {
    backgroundColor: colors.warning,
    animation: `${animations.pulse} 2s ${motion.easeInOut} infinite`,
  },
  
  reconnecting: {
    backgroundColor: colors.warning,
    animation: `${animations.pulse} 2s ${motion.easeInOut} infinite`,
  },
  
  disconnected: {
    backgroundColor: colors.gray500,
  },
  
  error: {
    backgroundColor: colors.danger,
  },
  
  icon: {
    fontSize: typography.textXs,
  },
  
  text: {
    fontSize: typography.textSm,
  },
  
  details: {
    fontSize: typography.textXs,
    opacity: 0.75,
  },
  
  aiNotification: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: spacing.xs,
    fontSize: typography.textXs,
    color: colors.gray600,
    backgroundColor: 'rgba(255, 193, 7, 0.1)',
    paddingTop: spacing.xs,
    paddingBottom: spacing.xs,
    paddingLeft: spacing.md,
    paddingRight: spacing.md,
    borderRadius: layout.radiusFull,
    border: `1px solid ${colors.warning}`,
  },
  
  aiIcon: {
    marginRight: spacing.xs,
  },
});

const ConnectionIndicator = ({
  isConnected = false,
  isConnecting = false,
  isReconnecting = false,
  error = null,
  roomId = null,
  showDetails = false,
  className = '',
  disconnectedPlayers = [],
}) => {
  const getStatusInfo = () => {
    if (error) {
      return {
        status: 'error',
        text: 'Connection Error',
        style: styles.error,
        icon: '❌',
      };
    }

    if (isReconnecting) {
      return {
        status: 'reconnecting',
        text: 'Reconnecting...',
        style: styles.reconnecting,
        icon: '🔄',
      };
    }

    if (isConnecting) {
      return {
        status: 'connecting',
        text: 'Connecting...',
        style: styles.connecting,
        icon: '⚡',
      };
    }

    if (isConnected) {
      return {
        status: 'connected',
        text: 'Connected',
        style: styles.connected,
        icon: '✅',
      };
    }

    return {
      status: 'disconnected',
      text: 'Disconnected',
      style: styles.disconnected,
      icon: '⚫',
    };
  };

  const statusInfo = getStatusInfo();
  const hasDisconnectedPlayers = disconnectedPlayers.length > 0;

  // Apply indicator styles
  const indicatorProps = stylex.props(
    styles.indicator,
    statusInfo.style
  );

  // During migration, allow combining with existing CSS classes
  const combinedIndicatorProps = className 
    ? { ...indicatorProps, className: `${indicatorProps.className || ''} ${className}`.trim() }
    : indicatorProps;

  return (
    <div {...stylex.props(styles.container)}>
      <div {...combinedIndicatorProps}>
        <span {...stylex.props(styles.icon)}>{statusInfo.icon}</span>
        <span {...stylex.props(styles.text)}>{statusInfo.text}</span>

        {showDetails && roomId && (
          <span {...stylex.props(styles.details)}>({roomId})</span>
        )}

        {error && showDetails && (
          <span 
            {...stylex.props(styles.details)} 
            title={error.message || error}
          >
            ⚠️
          </span>
        )}
      </div>

      {hasDisconnectedPlayers && (
        <div {...stylex.props(styles.aiNotification)}>
          <span {...stylex.props(styles.aiIcon)}>🤖</span>
          AI Playing for: {disconnectedPlayers.join(', ')} - Can reconnect anytime
        </div>
      )}
    </div>
  );
};

export default ConnectionIndicator;