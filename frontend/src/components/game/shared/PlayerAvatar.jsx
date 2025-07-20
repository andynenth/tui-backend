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
 */
const PlayerAvatar = ({ name, isBot = false, isThinking = false, className = '', size = 'medium', theme = 'default' }) => {
  // Debug log for avatar changes
  console.log(`🎭 PlayerAvatar: ${name} - isBot=${isBot}, isThinking=${isThinking}`);

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

  // Render bot avatar
  if (isBot) {
    return (
      <div className={`player-avatar player-avatar--bot ${getSizeClass()} ${getThemeClass()} ${isThinking ? 'thinking' : ''} ${className}`}>
        <img src={BotIcon} alt="Bot" className="bot-icon" />
      </div>
    );
  }

  // Render human avatar
  return (
    <div className={`player-avatar ${getSizeClass()} ${getThemeClass()} ${className}`}>
      <img src={HumanIcon} alt={name} className="human-icon" />
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
};

export default PlayerAvatar;
