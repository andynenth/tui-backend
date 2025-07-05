/**
 * 🎯 **EnhancedGamePiece** - Unified Game Piece Component with Chinese Character Support
 * 
 * Features:
 * ✅ Consistent color-matched borders (red/black pieces)
 * ✅ Chinese character support with SimSun font
 * ✅ Multiple size variants (small, medium, large)
 * ✅ Selection states with ring indicators
 * ✅ Gradient backgrounds for depth
 * ✅ Proper click handling and accessibility
 * ✅ Consistent styling across all game phases
 */

import React from 'react';
import PropTypes from 'prop-types';

/**
 * Enhanced game piece component with unified styling
 * Supports Chinese characters, multiple sizes, and consistent color schemes
 */
export function EnhancedGamePiece({ 
  piece, 
  isSelected = false, 
  onClick, 
  size = 'medium', 
  disabled = false,
  className = '' 
}) {
  // Size configuration
  const sizeClasses = {
    small: 'w-4 h-4 text-xs',
    medium: 'w-6 h-6 text-sm', 
    large: 'w-8 h-8 text-base'
  };
  
  // Determine piece color and styling
  const isRed = piece.color === 'red';
  const pieceContent = piece.display || piece.character || piece.value || '?';
  
  // Build className string
  const combinedClassName = `
    ${sizeClasses[size]} rounded-full bg-gradient-to-br from-white to-gray-50 
    flex items-center justify-center font-bold border-2 shadow-sm
    transition-all duration-200 ease-in-out
    ${!disabled ? 'cursor-pointer hover:shadow-md hover:scale-105' : 'cursor-not-allowed opacity-60'}
    ${isSelected ? 'ring-2 ring-blue-400 ring-offset-1 scale-110' : ''}
    ${isRed ? 'text-red-600 border-red-300' : 'text-gray-600 border-gray-400'}
    ${className}
  `;
  
  const handleClick = () => {
    if (!disabled && onClick) {
      onClick(piece);
    }
  };
  
  return (
    <div
      onClick={handleClick}
      className={combinedClassName}
      style={{ 
        fontFamily: 'SimSun, serif',
        borderColor: isRed ? 'rgba(220, 38, 38, 0.4)' : 'rgba(73, 80, 87, 0.4)'
      }}
      role={onClick ? 'button' : 'presentation'}
      tabIndex={onClick && !disabled ? 0 : -1}
      aria-label={`${piece.color} piece: ${pieceContent}${piece.points ? ` (${piece.points} points)` : ''}`}
      onKeyDown={(e) => {
        if ((e.key === 'Enter' || e.key === ' ') && !disabled && onClick) {
          e.preventDefault();
          onClick(piece);
        }
      }}
    >
      {pieceContent}
    </div>
  );
}

// PropTypes definition
EnhancedGamePiece.propTypes = {
  piece: PropTypes.shape({
    color: PropTypes.oneOf(['red', 'black']).isRequired,
    display: PropTypes.string,
    character: PropTypes.string,
    value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    points: PropTypes.number
  }).isRequired,
  isSelected: PropTypes.bool,
  onClick: PropTypes.func,
  size: PropTypes.oneOf(['small', 'medium', 'large']),
  disabled: PropTypes.bool,
  className: PropTypes.string
};

EnhancedGamePiece.defaultProps = {
  isSelected: false,
  onClick: null,
  size: 'medium',
  disabled: false,
  className: ''
};

export default EnhancedGamePiece;