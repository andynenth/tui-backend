// frontend/src/components/EnhancedPlayerAvatar.stylex.jsx

import React, { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, motion, layout, shadows } from '../design-system/tokens.stylex';
import PlayerAvatar from './game/shared/PlayerAvatar';
import HostIndicator from './HostIndicator';
import ConnectionQuality from './ConnectionQuality';

// Animations
const fadeIn = stylex.keyframes({
  '0%': {
    opacity: 0,
  },
  '100%': {
    opacity: 1,
  },
});

const stateChange = stylex.keyframes({
  '0%': {
    transform: 'scale(1)',
    opacity: 1,
  },
  '50%': {
    transform: 'scale(0.9)',
    opacity: 0.7,
  },
  '100%': {
    transform: 'scale(1)',
    opacity: 1,
  },
});

const botPulse = stylex.keyframes({
  '0%': {
    boxShadow: '0 0 0 0 rgba(59, 130, 246, 0.5)',
  },
  '70%': {
    boxShadow: '0 0 0 10px rgba(59, 130, 246, 0)',
  },
  '100%': {
    boxShadow: '0 0 0 0 rgba(59, 130, 246, 0)',
  },
});

const spin = stylex.keyframes({
  '0%': {
    transform: 'rotate(0deg)',
  },
  '100%': {
    transform: 'rotate(360deg)',
  },
});

// EnhancedPlayerAvatar styles
const styles = stylex.create({
  container: {
    position: 'relative',
    display: 'inline-block',
  },
  
  avatarTransition: {
    transition: `all '300ms' 'cubic-bezier(0.4, 0, 0.2, 1)'`,
  },
  
  stateChange: {
    animation: `${stateChange} 0.5s 'cubic-bezier(0.4, 0, 0.2, 1)'`,
  },
  
  disconnected: {
    opacity: 0.7,
    filter: 'grayscale(0.3)',
  },
  
  botActive: {
    animation: `${botPulse} 2s infinite`,
    borderRadius: '9999px',
  },
  
  hostIndicator: {
    position: 'absolute',
    top: '-8px',
    right: '-8px',
    animation: `${fadeIn} 0.3s 'cubic-bezier(0, 0, 0.2, 1)'`,
  },
  
  disconnectBadge: {
    position: 'absolute',
    bottom: '-4px',
    right: '-4px',
    animation: `${fadeIn} 0.3s 'cubic-bezier(0, 0, 0.2, 1)'`,
  },
  
  aiBadge: {
    display: 'inline-flex',
    alignItems: 'center',
    paddingTop: '2px',
    paddingBottom: '2px',
    paddingLeft: '6px',
    paddingRight: '6px',
    borderRadius: '9999px',
    fontSize: '0.75rem',
    fontWeight: '500',
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
    color: '#dc3545',
    borderWidth: '1px',
    borderStyle: 'solid',
    borderColor: '#dc3545',
  },
  
  connectionQuality: {
    position: 'absolute',
    bottom: '-8px',
    left: '50%',
    transform: 'translateX(-50%)',
  },
  
  qualityWrapper: {
    backgroundColor: '#ffffff',
    borderRadius: '0.125rem',
    padding: '2px 4px',
    boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  },
  
  reconnectingOverlay: {
    position: 'absolute',
    inset: 0,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    pointerEvents: 'none',
  },
  
  reconnectingSpinner: {
    width: '32px',
    height: '32px',
    color: '#0d6efd',
    opacity: 0.8,
    animation: `${spin} 1s linear infinite`,
  },
  
  spinnerCircle: {
    opacity: 0.25,
  },
  
  spinnerPath: {
    opacity: 0.75,
  },
});

/**
 * EnhancedPlayerAvatar Component
 *
 * Wraps PlayerAvatar with smooth transitions for bot/human switches
 * and connection state changes
 */
const EnhancedPlayerAvatar = ({
  player,
  isHost = false,
  showConnectionQuality = false,
  roomId,
  size = 'medium',
  className = '',
}) => {
  const [previousState, setPreviousState] = useState({
    isBot: player.is_bot,
    isConnected: player.is_connected !== false,
  });
  const [isTransitioning, setIsTransitioning] = useState(false);

  useEffect(() => {
    // Detect state changes
    const botStateChanged = previousState.isBot !== player.is_bot;
    const connectionStateChanged =
      previousState.isConnected !== (player.is_connected !== false);

    if (botStateChanged || connectionStateChanged) {
      setIsTransitioning(true);
      setPreviousState({
        isBot: player.is_bot,
        isConnected: player.is_connected !== false,
      });

      // Reset transition state after animation
      const timer = setTimeout(() => {
        setIsTransitioning(false);
      }, 500);

      return () => clearTimeout(timer);
    }
  }, [player.is_bot, player.is_connected, previousState]);

  const isDisconnected = player.is_bot && player.original_is_bot === false;

  // Apply container styles
  const containerProps = stylex.props(styles.container);
  
  // During migration, allow combining with existing CSS classes
  const combinedContainerProps = className 
    ? { ...containerProps, className: `${containerProps.className || ''} ${className}`.trim() }
    : containerProps;

  return (
    <div {...combinedContainerProps}>
      {/* Player Avatar with transitions */}
      <div
        {...stylex.props(
          styles.avatarTransition,
          isTransitioning && styles.stateChange,
          isDisconnected && styles.disconnected,
          player.is_bot && isTransitioning && styles.botActive
        )}
      >
        <PlayerAvatar
          player={player}
          isBot={player.is_bot}
          thinking={player.is_bot && player.is_thinking}
          size={size}
        />
      </div>

      {/* Host Indicator */}
      {isHost && (
        <div {...stylex.props(styles.hostIndicator)}>
          <HostIndicator isHost={true} size="small" />
        </div>
      )}

      {/* Disconnect Badge with smooth transition */}
      {isDisconnected && (
        <div {...stylex.props(styles.disconnectBadge)}>
          <span {...stylex.props(styles.aiBadge)}>
            AI
          </span>
        </div>
      )}

      {/* Connection Quality Indicator */}
      {showConnectionQuality && roomId && !player.is_bot && (
        <div {...stylex.props(styles.connectionQuality)}>
          <div {...stylex.props(styles.qualityWrapper)}>
            <ConnectionQuality
              roomId={roomId}
              size="small"
              showLatency={false}
            />
          </div>
        </div>
      )}

      {/* Reconnection Animation */}
      {player.is_reconnecting && (
        <div {...stylex.props(styles.reconnectingOverlay)}>
          <svg
            {...stylex.props(styles.reconnectingSpinner)}
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              {...stylex.props(styles.spinnerCircle)}
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              {...stylex.props(styles.spinnerPath)}
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        </div>
      )}
    </div>
  );
};

EnhancedPlayerAvatar.propTypes = {
  player: PropTypes.shape({
    name: PropTypes.string.isRequired,
    is_bot: PropTypes.bool,
    is_connected: PropTypes.bool,
    original_is_bot: PropTypes.bool,
    is_thinking: PropTypes.bool,
    is_reconnecting: PropTypes.bool,
  }).isRequired,
  isHost: PropTypes.bool,
  showConnectionQuality: PropTypes.bool,
  roomId: PropTypes.string,
  size: PropTypes.oneOf(['small', 'medium', 'large']),
  className: PropTypes.string,
};

export default EnhancedPlayerAvatar;