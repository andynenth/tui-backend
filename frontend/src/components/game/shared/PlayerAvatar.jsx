import React from 'react';
import PropTypes from 'prop-types';

// SVG imports
import BotIcon from '../../../assets/avatars/bot.svg';
import HumanIcon from '../../../assets/avatars/human.svg';

// Connection status components
import ConnectionStatusBadge from '../../ConnectionStatusBadge';
import DisconnectOverlay from '../../DisconnectOverlay';
import useDisconnectStatus from '../../../hooks/useDisconnectStatus';

/**
 * PlayerAvatar Component
 *
 * A reusable component that displays player initials in a circular avatar.
 * For bot players, displays a robot icon instead of initials.
 * Extracts the common avatar pattern used across game phases.
 *
 * @param {string} name - The player's name (required)
 * @param {boolean} isBot - Whether the player is a bot (optional, default: false)
 * @param {boolean} isThinking - Whether the bot is currently thinking (optional, default: false)
 * @param {string} className - Additional CSS class names (optional)
 * @param {string} size - Avatar size: 'mini', 'small', 'medium', 'large' (default: 'medium')
 * @param {string} theme - Avatar theme: 'default', 'yellow' (default: 'default')
 * @param {boolean} isDisconnected - Whether the player is disconnected (optional, default: false)
 * @param {string} connectionStatus - Connection status: 'connected', 'disconnected', 'reconnecting' (optional)
 * @param {boolean} showConnectionStatus - Whether to show connection status indicators (optional, default: true)
 * @param {boolean} showDisconnectOverlay - Whether to show disconnect overlay (optional, default: true)
 */
const PlayerAvatar = ({ 
  name, 
  isBot = false, 
  isThinking = false, 
  className = '', 
  size = 'medium', 
  theme = 'default',
  isDisconnected = false,
  connectionStatus: propConnectionStatus,
  showConnectionStatus = true,
  showDisconnectOverlay = true
}) => {
  // Use hook for dynamic connection status if not provided as prop
  const hookConnectionData = useDisconnectStatus(name);
  const connectionStatus = propConnectionStatus || hookConnectionData.connectionStatus;
  const isActuallyDisconnected = isDisconnected || hookConnectionData.isDisconnected;
  const isBotPlaying = isBot || hookConnectionData.isBot;

  // Get size-specific class
  const getSizeClass = () => {
    switch (size) {
      case 'mini':
        return 'player-avatar--mini';
      case 'small':
        return 'player-avatar--small';
      case 'large':
        return 'player-avatar--large';
      default:
        return 'player-avatar--medium';
    }
  };

  // Get theme-specific class
  const getThemeClass = () => {
    return theme === 'yellow' ? 'player-avatar--yellow' : '';
  };

  // Get avatar content
  const getAvatarContent = () => {
    if (isBotPlaying) {
      return (
        <div className={`player-avatar player-avatar--bot ${getSizeClass()} ${getThemeClass()} ${isThinking ? 'thinking' : ''} ${isActuallyDisconnected ? 'player-avatar--disconnected' : ''} ${className}`}>
          <img src={BotIcon} alt="Bot" className="bot-icon" />
        </div>
      );
    }

    return (
      <div className={`player-avatar ${getSizeClass()} ${getThemeClass()} ${isActuallyDisconnected ? 'player-avatar--disconnected' : ''} ${className}`}>
        <img src={HumanIcon} alt={name} className="human-icon" />
      </div>
    );
  };

  // Render with connection status wrapper
  return (
    <div className="player-avatar-wrapper">
      {getAvatarContent()}
      {showConnectionStatus && (
        <ConnectionStatusBadge 
          connectionStatus={connectionStatus} 
          isBot={isBotPlaying && isActuallyDisconnected} 
        />
      )}
      {showDisconnectOverlay && isActuallyDisconnected && (
        <DisconnectOverlay
          isDisconnected={isActuallyDisconnected}
          connectionStatus={connectionStatus}
          playerName={name}
          isBot={isBotPlaying}
        />
      )}
    </div>
  );
};

PlayerAvatar.propTypes = {
  name: PropTypes.string.isRequired,
  isBot: PropTypes.bool,
  isThinking: PropTypes.bool,
  className: PropTypes.string,
  size: PropTypes.oneOf(['mini', 'small', 'medium', 'large']),
  theme: PropTypes.oneOf(['default', 'yellow']),
  isDisconnected: PropTypes.bool,
  connectionStatus: PropTypes.oneOf(['connected', 'disconnected', 'reconnecting']),
  showConnectionStatus: PropTypes.bool,
  showDisconnectOverlay: PropTypes.bool,
};

export default PlayerAvatar;
