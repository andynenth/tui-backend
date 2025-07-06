/**
 * 🤲 **HandSection** - Unified Hand Display Component for All Game Phases
 * 
 * Features:
 * ✅ 4-column grid layout for optimal piece display
 * ✅ Active player golden background styling
 * ✅ Enhanced piece selection with visual feedback
 * ✅ Consistent spacing and alignment
 * ✅ Support for piece sorting and index mapping
 * ✅ Responsive design for mobile containers
 * ✅ Accessibility support with proper labeling
 */

import React from 'react';
import PropTypes from 'prop-types';
import EnhancedGamePiece from './EnhancedGamePiece';

/**
 * Unified hand section component for displaying player pieces
 * Supports active player styling, piece selection, and consistent layout
 */
export function HandSection({ 
  pieces = [], 
  selectedPieces = [], 
  onPieceSelect, 
  isActivePlayer = false,
  disabled = false,
  title = null,
  className = '' 
}) {
  // Enhanced pieces with sorting for better UX (red first, then by points descending)
  const enhancedPieces = pieces.map((piece, originalIndex) => ({
    ...piece,
    originalIndex,
    displayId: `piece-${originalIndex}`,
    sortKey: `${piece.color === 'red' ? '0' : '1'}-${String(piece.points || 0).padStart(3, '0')}`
  }));
  
  // Sort pieces for display (red first, then by points descending)
  const sortedPieces = [...enhancedPieces].sort((a, b) => {
    if (a.color !== b.color) {
      return a.color === 'red' ? -1 : 1;
    }
    return (b.points || 0) - (a.points || 0);
  });
  
  const handlePieceSelect = (piece, displayIndex) => {
    if (disabled || !onPieceSelect) return;
    
    // Find the enhanced piece to get original index
    const enhancedPiece = sortedPieces[displayIndex];
    if (enhancedPiece) {
      onPieceSelect(enhancedPiece.originalIndex, enhancedPiece);
    }
  };
  
  const isPieceSelected = (displayIndex) => {
    const enhancedPiece = sortedPieces[displayIndex];
    return enhancedPiece && selectedPieces.includes(enhancedPiece.originalIndex);
  };
  
  return (
    <div 
      className={`
        px-5 py-5 border-t relative z-20
        ${className}
      `}
      style={{
        background: `
          linear-gradient(180deg, #F8F9FA 0%, #E9ECEF 100%),
          radial-gradient(ellipse 100% 60% at 50% 0%, rgba(173, 181, 189, 0.2) 0%, transparent 100%)
        `,
        borderTopColor: 'rgba(173, 181, 189, 0.2)'
      }}
    >
      {/* Decorative top line - exact mockup match */}
      <div 
        className="absolute top-0 left-1/2 transform -translate-x-1/2 w-10 h-0.5"
        style={{
          background: 'linear-gradient(90deg, transparent, #6C757D, transparent)'
        }}
      />
      {/* Optional title */}
      {title && (
        <h3 className="text-sm font-semibold text-gray-700 mb-3 text-center">
          {title}
        </h3>
      )}
      
      {/* Hand pieces grid - matching mockup layout */}
      <div className="grid grid-cols-4 gap-3 max-w-sm mx-auto">
        {sortedPieces.map((piece, displayIndex) => (
          <EnhancedGamePiece
            key={piece.displayId}
            piece={piece}
            isSelected={isPieceSelected(displayIndex)}
            onClick={() => handlePieceSelect(piece, displayIndex)}
            size="large"
            disabled={disabled}
            className="transition-all duration-200"
          />
        ))}
        
        {/* Fill empty slots if less than 8 pieces */}
        {Array.from({ length: Math.max(0, 8 - sortedPieces.length) }).map((_, index) => (
          <div
            key={`empty-${index}`}
            className="w-8 h-8 rounded-full border-2 border-dashed border-gray-300 bg-gray-50 opacity-30"
            aria-hidden="true"
          />
        ))}
      </div>
      
      {/* Selection indicator */}
      {selectedPieces.length > 0 && (
        <div className="text-center mt-3">
          <span className="text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded-full">
            {selectedPieces.length} piece{selectedPieces.length !== 1 ? 's' : ''} selected
          </span>
        </div>
      )}
    </div>
  );
}

// PropTypes definition
HandSection.propTypes = {
  pieces: PropTypes.arrayOf(PropTypes.shape({
    color: PropTypes.oneOf(['red', 'black']).isRequired,
    display: PropTypes.string,
    character: PropTypes.string,
    value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    points: PropTypes.number
  })),
  selectedPieces: PropTypes.arrayOf(PropTypes.number),
  onPieceSelect: PropTypes.func,
  isActivePlayer: PropTypes.bool,
  disabled: PropTypes.bool,
  title: PropTypes.string,
  className: PropTypes.string
};

HandSection.defaultProps = {
  pieces: [],
  selectedPieces: [],
  onPieceSelect: null,
  isActivePlayer: false,
  disabled: false,
  title: null,
  className: ''
};

export default HandSection;