import React from 'react';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, motion, layout } from '../design-system/tokens.stylex';
import { animations } from '../design-system/utils.stylex';

// Connection indicator styles
const styles = stylex.create({
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
  },
  
  indicator: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.5rem',
    paddingTop: '0.25rem',
    paddingBottom: '0.25rem',
    paddingLeft: '1rem',
    paddingRight: '1rem',
    borderRadius: '9999px',
    fontSize: '0.875rem',
    fontWeight: '500',
    color: '#ffffff',
    transition: `all '300ms' 'cubic-bezier(0.4, 0, 0.2, 1)'`,
  },
  
  // Status variants
  connected: {
    backgroundColor: '#198754',
  },
  
  connecting: {
    backgroundColor: '#ffc107',
    animation: `${animations.pulse} 2s 'cubic-bezier(0.4, 0, 0.2, 1)' infinite`,
  },
  
  reconnecting: {
    backgroundColor: '#ffc107',
    animation: `${animations.pulse} 2s 'cubic-bezier(0.4, 0, 0.2, 1)' infinite`,
  },
  
  disconnected: {
    backgroundColor: '#adb5bd',
  },
  
  error: {
    backgroundColor: '#dc3545',
  },
  
  icon: {
    fontSize: '0.75rem',
  },
  
  text: {
    fontSize: '0.875rem',
  },
  
  details: {
    fontSize: '0.75rem',
    opacity: 0.75,
  },
  
  aiNotification: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.25rem',
    fontSize: '0.75rem',
    color: '#6c757d',
    backgroundColor: 'rgba(255, 193, 7, 0.1)',
    paddingTop: '0.25rem',
    paddingBottom: '0.25rem',
    paddingLeft: '1rem',
    paddingRight: '1rem',
    borderRadius: '9999px',
    borderWidth: '1px',
    borderStyle: 'solid',
    borderColor: '#ffc107',
  },
  
  aiIcon: {
    marginRight: '0.25rem',
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