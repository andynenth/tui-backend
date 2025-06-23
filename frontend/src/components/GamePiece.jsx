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
      cursor-pointer select-none transition-all duration-200 font-mono
      ${sizeClasses[size]}
    `;
  };

  const getColorClasses = () => {
    if (isRed) {
      return `
        bg-red-50 border-red-300 text-red-800
        ${isPlayable ? 'hover:bg-red-100 hover:border-red-400' : ''}
      `;
    } else {
      return `
        bg-gray-800 border-gray-600 text-gray-100
        ${isPlayable ? 'hover:bg-gray-700 hover:border-gray-500' : ''}
      `;
    }
  };

  const getStateClasses = () => {
    let classes = '';
    
    if (isSelected) {
      classes += ' ring-2 ring-blue-500 bg-blue-100 border-blue-400';
    }
    
    if (isHighlighted) {
      classes += ' ring-2 ring-yellow-400 shadow-lg';
    }
    
    if (!isPlayable) {
      classes += ' opacity-50 cursor-not-allowed grayscale';
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
        <div className="absolute top-0 right-0 w-3 h-3 bg-blue-500 rounded-full transform translate-x-1 -translate-y-1">
          <div className="w-full h-full bg-white rounded-full scale-50"></div>
        </div>
      )}
    </div>
  );
};

const getPieceSymbol = (kind) => {
  const symbols = {
    'GENERAL_RED': '将',
    'GENERAL_BLACK': '將', 
    'ADVISOR_RED': '士',
    'ADVISOR_BLACK': '仕',
    'ELEPHANT_RED': '相',
    'ELEPHANT_BLACK': '象',
    'CHARIOT_RED': '車',
    'CHARIOT_BLACK': '車',
    'HORSE_RED': '馬',
    'HORSE_BLACK': '馬',
    'CANNON_RED': '炮',
    'CANNON_BLACK': '砲',
    'SOLDIER_RED': '兵',
    'SOLDIER_BLACK': '卒'
  };
  
  return symbols[kind] || '?';
};

export default GamePiece;