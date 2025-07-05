/**
 * 📱 **GamePhaseContainer** - Unified Mobile Container for All Game Phases
 * 
 * Features:
 * ✅ Fixed 9:16 aspect ratio mobile-first design
 * ✅ Consistent background gradients and paper texture
 * ✅ Subtle inner glow effects for depth
 * ✅ Rounded design with shadows and borders
 * ✅ Flexbox layout for proper content distribution
 * ✅ Overflow handling for mobile screens
 */

import React from 'react';
import PropTypes from 'prop-types';

/**
 * Unified container component for all game phases
 * Provides consistent mobile-first styling across preparation, declaration, turn, and results phases
 */
export function GamePhaseContainer({ children, className = '' }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-100 via-gray-200 to-gray-300 flex items-center justify-center overflow-hidden relative">
      {/* Subtle paper texture overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-white/10 via-transparent to-black/5 pointer-events-none"></div>
      
      {/* Fixed 9:16 Container */}
      <div className={`
        w-full max-w-sm h-screen max-h-[711px] 
        bg-gradient-to-br from-white to-gray-50 
        rounded-3xl border border-gray-300 shadow-2xl 
        flex flex-col relative overflow-hidden
        ${className}
      `}>
        {/* Subtle inner glow for depth and warmth */}
        <div className="absolute inset-0 bg-gradient-to-br from-yellow-50/30 via-transparent to-blue-50/20 pointer-events-none"></div>
        
        {/* Phase content with proper z-index */}
        <div className="relative z-10 flex flex-col h-full">
          {children}
        </div>
      </div>
    </div>
  );
}

// PropTypes definition
GamePhaseContainer.propTypes = {
  children: PropTypes.node.isRequired,
  className: PropTypes.string
};

GamePhaseContainer.defaultProps = {
  className: ''
};

export default GamePhaseContainer;