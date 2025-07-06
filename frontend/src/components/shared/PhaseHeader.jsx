/**
 * 📊 **PhaseHeader** - Unified Header Component for All Game Phases
 * 
 * Features:
 * ✅ Consistent serif typography (Crimson Pro)
 * ✅ Round indicator system with white circles
 * ✅ Decorative line separator under header
 * ✅ Subtitle formatting with phase information
 * ✅ Gradient background with proper spacing
 * ✅ Responsive design for mobile containers
 */

import React from 'react';
import PropTypes from 'prop-types';

/**
 * Unified header component for all game phases
 * Provides consistent styling and layout for phase titles and information
 */
export function PhaseHeader({ 
  title, 
  subtitle, 
  roundNumber = 1, 
  showRoundIndicator = true,
  className = '' 
}) {
  return (
    <div className={`
      text-center pt-12 pb-4 px-6 
      bg-gradient-to-b from-gray-50/80 to-transparent 
      border-b border-gray-200 relative
      ${className}
    `}>
      {/* Decorative line separator */}
      <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-10 h-0.5 bg-gradient-to-r from-transparent via-gray-400 to-transparent"></div>
      
      {/* Phase title with exact mockup styling */}
      <h1 
        className="font-bold text-gray-800 mb-1"
        style={{
          fontFamily: 'Crimson Pro, serif',
          fontSize: '28px',
          fontWeight: '700',
          color: '#343A40',
          letterSpacing: '-0.5px',
          marginBottom: '4px'
        }}
      >
        {title}
      </h1>
      
      {/* Subtitle with exact mockup styling */}
      <p 
        className="flex items-center justify-center"
        style={{
          fontSize: '14px',
          color: '#6C757D',
          fontWeight: '500'
        }}
      >
        {showRoundIndicator && (
          <span className="inline-block w-4 h-4 bg-white border-2 border-gray-300 rounded-full mr-2"></span>
        )}
        {showRoundIndicator ? `Round ${roundNumber} • ${subtitle}` : subtitle}
      </p>
    </div>
  );
}

// PropTypes definition
PhaseHeader.propTypes = {
  title: PropTypes.string.isRequired,
  subtitle: PropTypes.string.isRequired,
  roundNumber: PropTypes.number,
  showRoundIndicator: PropTypes.bool,
  className: PropTypes.string
};

PhaseHeader.defaultProps = {
  roundNumber: 1,
  showRoundIndicator: true,
  className: ''
};

export default PhaseHeader;