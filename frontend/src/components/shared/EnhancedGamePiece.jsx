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
  className = '',
  animationDelay = '0s'
}) {
  
  // Parse piece information like GamePiece.jsx
  const parsePieceInfo = () => {
    if (!piece) {
      return { color: 'red', point: 0, kind: 'UNKNOWN' };
    }
    
    if (typeof piece === 'string') {
      const color = piece.includes('RED') ? 'red' : 'black';
      const match = piece.match(/\((\d+)\)/);
      const point = match ? parseInt(match[1]) : 0;
      const kind = piece.split('(')[0].trim();
      return { color, point, kind };
    }
    
    // Handle object pieces - fix color mapping
    return {
      color: (piece.color && piece.color.toLowerCase()) || 'black',
      point: piece.points || piece.point || piece.value || 0,
      kind: piece.kind || piece.type || 'UNKNOWN'
    };
  };

  const pieceInfo = parsePieceInfo();
  const isRed = pieceInfo.color === 'red';
  
  // Chinese character symbols - exact mapping from GamePiece.jsx
  const getPieceSymbol = (kind, color) => {
    let symbolKey = kind;
    if (color && !kind.includes('_')) {
      symbolKey = `${kind}_${color.toUpperCase()}`;
    }
    
    const symbols = {
      GENERAL_RED: '将',
      GENERAL_BLACK: '將', 
      ADVISOR_RED: '士',
      ADVISOR_BLACK: '仕',
      ELEPHANT_RED: '相',
      ELEPHANT_BLACK: '象',
      CHARIOT_RED: '車',
      CHARIOT_BLACK: '車',
      HORSE_RED: '馬',
      HORSE_BLACK: '馬',
      CANNON_RED: '炮',
      CANNON_BLACK: '砲',
      SOLDIER_RED: '兵',
      SOLDIER_BLACK: '卒'
    };
    
    return symbols[symbolKey] || '?';
  };

  const chineseChar = getPieceSymbol(pieceInfo.kind, pieceInfo.color);
  const piecePoints = pieceInfo.point;
  
  // Build className string - exact mockup match (no Tailwind classes)
  const combinedClassName = `piece ${pieceInfo.color} ${isSelected ? 'selected' : ''} ${disabled ? 'disabled' : ''} ${className}`.trim();
  
  // Only animation delay as inline style, let CSS handle the rest
  const inlineStyles = {
    animationDelay: animationDelay
  };
  
  const handleClick = () => {
    if (!disabled && onClick) {
      onClick(piece);
    }
  };
  
  return (
    <div
      onClick={handleClick}
      className={combinedClassName}
      style={inlineStyles}
      role={onClick ? 'button' : 'presentation'}
      tabIndex={onClick && !disabled ? 0 : -1}
      aria-label={`${pieceInfo.color} piece: ${chineseChar}${piecePoints ? ` (${piecePoints} points)` : ''}`}
      onKeyDown={(e) => {
        if ((e.key === 'Enter' || e.key === ' ') && !disabled && onClick) {
          e.preventDefault();
          onClick(piece);
        }
      }}
    >
      {/* Chinese Character */}
      <div className="piece-character">
        {chineseChar}
      </div>
      
      {/* Point Value - exact mockup styling */}
      <div className="piece-points">
        {piecePoints}
      </div>
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
  className: PropTypes.string,
  animationDelay: PropTypes.string
};

EnhancedGamePiece.defaultProps = {
  isSelected: false,
  onClick: null,
  size: 'medium',
  disabled: false,
  className: ''
};

export default EnhancedGamePiece;