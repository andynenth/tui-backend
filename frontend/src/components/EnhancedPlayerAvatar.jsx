// frontend/src/components/EnhancedPlayerAvatar.jsx

import React, { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import PlayerAvatar from './game/shared/PlayerAvatar';
import HostIndicator from './HostIndicator';
import ConnectionQuality from './ConnectionQuality';
import '../styles/connection-animations.css';

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

  return (
    <div className={`relative inline-block ${className}`}>
      {/* Player Avatar with transitions */}
      <div
        className={`
        player-avatar-transition
        ${isTransitioning ? 'player-state-change' : ''}
        ${isDisconnected ? 'player-disconnected' : ''}
        ${player.is_bot && isTransitioning ? 'player-bot-active' : ''}
      `}
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
        <div className="absolute -top-2 -right-2 host-crown-appear">
          <HostIndicator isHost={true} size="small" />
        </div>
      )}

      {/* Disconnect Badge with smooth transition */}
      {isDisconnected && (
        <div className="absolute -bottom-1 -right-1 animate-fadeIn">
          <span className="inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
            AI
          </span>
        </div>
      )}

      {/* Connection Quality Indicator */}
      {showConnectionQuality && roomId && !player.is_bot && (
        <div className="absolute -bottom-2 left-1/2 transform -translate-x-1/2">
          <ConnectionQuality
            roomId={roomId}
            size="small"
            showLatency={false}
            className="bg-white rounded px-1"
          />
        </div>
      )}

      {/* Reconnection Animation */}
      {player.is_reconnecting && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="reconnecting-spinner">
            <svg
              className="w-8 h-8 text-blue-500 opacity-80"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          </div>
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
