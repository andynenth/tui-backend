import React from 'react';

const GamePiece = ({ 
  piece, 
  isSelected = false, 
  isPlayable = true, 
  isHighlighted = false,
  size = 'md',
  onSelect,
  onDoubleClick,
  className = '' 
}) => {
  const handleClick = () => {
    if (isPlayable && onSelect) {
      onSelect(piece);
    }
  };

  const handleDoubleClick = () => {
    if (isPlayable && onDoubleClick) {
      onDoubleClick(piece);
    }
  };

  const parsePointFromString = (pieceStr) => {
    const match = pieceStr.match(/\((\d+)\)/);
    return match ? parseInt(match[1]) : 0;
  };

  const parsePieceInfo = () => {
    if (typeof piece === 'string') {
      const color = piece.includes('RED') ? 'RED' : 'BLACK';
      const point = parsePointFromString(piece);
      const kind = piece.split('(')[0].trim();
      return { color, point, kind };
    }
    return piece;
  };

  const pieceInfo = parsePieceInfo();
  const isRed = pieceInfo.color === 'RED';
  
  const sizeClasses = {
    sm: 'w-12 h-12 text-xs',
    md: 'w-16 h-16 text-sm', 
    lg: 'w-20 h-20 text-base'
  };

  const getBaseClasses = () => {
    return `
      relative flex flex-col items-center justify-center rounded-lg border-2 
      cursor-pointer select-none font-mono transform-gpu
      transition-all duration-300 ease-out
      ${isPlayable ? 'hover:scale-105 hover:shadow-lg active:scale-95' : ''}
      ${sizeClasses[size]}
    `;
  };

  const getColorClasses = () => {
    if (isRed) {
      return `
        bg-gradient-to-br from-red-50 to-red-100 border-red-300 text-red-800
        ${isPlayable ? 'hover:from-red-100 hover:to-red-200 hover:border-red-400 hover:shadow-red-200/50' : ''}
      `;
    } else {
      return `
        bg-gradient-to-br from-gray-800 to-gray-900 border-gray-600 text-gray-100
        ${isPlayable ? 'hover:from-gray-700 hover:to-gray-800 hover:border-gray-500 hover:shadow-gray-700/50' : ''}
      `;
    }
  };

  const getStateClasses = () => {
    let classes = '';
    
    if (isSelected) {
      classes += ' ring-4 ring-blue-500/70 ring-offset-2 ring-offset-white scale-110 z-10';
      classes += ' shadow-xl shadow-blue-500/30';
    }
    
    if (isHighlighted) {
      classes += ' ring-4 ring-yellow-400/80 ring-offset-2 shadow-xl shadow-yellow-400/30';
      classes += ' animate-pulse';
    }
    
    if (!isPlayable) {
      classes += ' opacity-50 cursor-not-allowed grayscale filter brightness-75';
    }
    
    return classes;
  };

  const classes = [
    getBaseClasses(),
    getColorClasses(),
    getStateClasses(),
    className
  ].filter(Boolean).join(' ');

  return (
    <div 
      className={classes}
      onClick={handleClick}
      onDoubleClick={handleDoubleClick}
      role="button"
      tabIndex={isPlayable ? 0 : -1}
      aria-pressed={isSelected}
      aria-disabled={!isPlayable}
      title={`${pieceInfo.kind} (${pieceInfo.point} points)`}
    >
      {/* Piece symbol */}
      <div className={`font-bold ${size === 'lg' ? 'text-xl' : size === 'sm' ? 'text-xs' : 'text-sm'}`}>
        {getPieceSymbol(pieceInfo.kind)}
      </div>
      
      {/* Point value */}
      <div className={`font-medium leading-none ${size === 'lg' ? 'text-xs' : 'text-xs'}`}>
        {pieceInfo.point}
      </div>

      {/* Selection indicator */}
      {isSelected && (
        <div className="absolute top-0 right-0 w-4 h-4 bg-blue-500 rounded-full transform translate-x-2 -translate-y-2 animate-bounce">
          <div className="w-full h-full bg-white rounded-full scale-50 animate-pulse"></div>
        </div>
      )}
      
      {/* Highlight glow effect */}
      {(isSelected || isHighlighted) && (
        <div className="absolute inset-0 rounded-lg bg-gradient-to-br from-transparent via-white/10 to-transparent pointer-events-none"></div>
      )}
    </div>
  );
};

const getPieceSymbol = (kind) => {
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
  
  return symbols[kind] || '?';
};

export default GamePiece;