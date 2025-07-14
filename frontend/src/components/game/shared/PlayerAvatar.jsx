import React from 'react';
import PropTypes from 'prop-types';

/**
 * PlayerAvatar Component
 *
 * A reusable component that displays player initials in a circular avatar.
 * Extracts the common avatar pattern used across game phases.
 *
 * @param {string} name - The player's name (required)
 * @param {string} className - Additional CSS class names (optional)
 * @param {string} size - Avatar size: 'small', 'medium', 'large' (default: 'medium')
 */
const PlayerAvatar = ({ name, className = '', size = 'medium' }) => {
  // Get player initial from name
  const getInitial = () => {
    if (!name || typeof name !== 'string') return '?';
    return name.charAt(0).toUpperCase();
  };

  // Get size-specific class
  const getSizeClass = () => {
    switch (size) {
      case 'small':
        return 'player-avatar--small';
      case 'large':
        return 'player-avatar--large';
      default:
        return 'player-avatar--medium';
    }
  };

  return (
    <div className={`player-avatar ${getSizeClass()} ${className}`}>
      {getInitial()}
    </div>
  );
};

PlayerAvatar.propTypes = {
  name: PropTypes.string.isRequired,
  className: PropTypes.string,
  size: PropTypes.oneOf(['small', 'medium', 'large']),
};

export default PlayerAvatar;
