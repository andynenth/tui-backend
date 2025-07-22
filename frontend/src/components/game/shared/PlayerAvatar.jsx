import React from 'react';
import PropTypes from 'prop-types';

// SVG imports
import BotIcon from '../../../assets/avatars/bot.svg';
import HumanIcon from '../../../assets/avatars/human.svg';

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
 * @param {boolean} showAIBadge - Whether to show AI playing badge (optional, default: false)
 * @param {string} avatarColor - Avatar color for human players (optional, default: null)
 */
const PlayerAvatar = ({
  name,
  isBot = false,
  isThinking = false,
  className = '',
  size = 'medium',
  theme = 'default',
  isDisconnected = false,
  showAIBadge = false,
  avatarColor = null,
}) => {
  // Debug logging
  console.log('🎨 PlayerAvatar received:', { name, isBot, avatarColor });
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

  // Get color class
  const getColorClass = () => {
    if (!isBot && avatarColor) {
      const colorClass = `player-avatar--color-${avatarColor}`;
      console.log(`🎨 PlayerAvatar ${name} color class:`, colorClass);
      return colorClass;
    }
    return '';
  };

  // Render bot avatar
  if (isBot) {
    return (
      <div className="player-avatar-wrapper">
        <div
          className={`player-avatar player-avatar--bot ${getSizeClass()} ${getThemeClass()} ${getColorClass()} ${isThinking ? 'thinking' : ''} ${isDisconnected ? 'disconnected' : ''} ${className}`}
        >
          <img src={BotIcon} alt="Bot" className="bot-icon" />
        </div>
        {showAIBadge && <div className="ai-badge">AI</div>}
      </div>
    );
  }

  // Render human avatar
  return (
    <div className="player-avatar-wrapper">
      <div
        className={`player-avatar ${getSizeClass()} ${getThemeClass()} ${getColorClass()} ${isDisconnected ? 'disconnected' : ''} ${className}`}
      >
        <img src={HumanIcon} alt={name} className="human-icon" />
      </div>
      {isDisconnected && <div className="disconnect-badge">🔴</div>}
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
  showAIBadge: PropTypes.bool,
  avatarColor: PropTypes.string,
};

export default PlayerAvatar;
