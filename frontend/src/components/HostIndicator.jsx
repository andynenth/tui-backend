// frontend/src/components/HostIndicator.jsx

import React from 'react';
import PropTypes from 'prop-types';

/**
 * HostIndicator Component
 * 
 * Displays a crown icon or "HOST" badge to indicate who is the current room host.
 * Can be used alongside player names or avatars.
 */
const HostIndicator = ({ isHost, size = 'medium', className = '' }) => {
  if (!isHost) return null;

  const getSizeClasses = () => {
    switch (size) {
      case 'small':
        return 'text-xs px-1.5 py-0.5';
      case 'large':
        return 'text-base px-3 py-1.5';
      default:
        return 'text-sm px-2 py-1';
    }
  };

  return (
    <span 
      className={`inline-flex items-center ${getSizeClasses()} bg-yellow-400 text-yellow-900 font-medium rounded ${className}`}
      title="Room Host"
    >
      <span className="mr-1">👑</span>
      <span>HOST</span>
    </span>
  );
};

HostIndicator.propTypes = {
  isHost: PropTypes.bool.isRequired,
  size: PropTypes.oneOf(['small', 'medium', 'large']),
  className: PropTypes.string,
};

export default HostIndicator;