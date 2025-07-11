import React from 'react';
import PropTypes from 'prop-types';
import GamePiece from './GamePiece';

/**
 * PieceTray Component
 * 
 * A unified component for displaying the player's hand of pieces.
 * Used across all game phases with consistent styling and behavior.
 * 
 * @param {Array} pieces - Array of piece objects to display
 * @param {string} variant - Display variant: 'default', 'active', or 'fixed' (default: 'default')
 * @param {function} onPieceClick - Click handler for pieces (receives piece and index)
 * @param {Array} selectedPieces - Array of selected piece IDs for highlighting
 * @param {boolean} showValues - Whether to show piece values (default: true)
 * @param {boolean} animateAppear - Whether to animate pieces appearing (default: false)
 * @param {string} className - Additional CSS classes for the container
 */
const PieceTray = ({
  pieces = [],
  variant = 'default',
  onPieceClick,
  selectedPieces = [],
  showValues = true,
  animateAppear = false,
  animationType = 'bounce',
  className = ''
}) => {
  // Build container class names
  const containerClasses = [
    'piece-tray',
    variant === 'active' && 'piece-tray--active',
    variant === 'fixed' && 'piece-tray--fixed',
    className
  ].filter(Boolean).join(' ');

  // Handle piece click
  const handlePieceClick = (piece, index) => {
    if (onPieceClick) {
      onPieceClick(piece, index);
    }
  };

  // Check if a piece is selected
  const isPieceSelected = (piece, index) => {
    if (!selectedPieces.length) return false;
    
    // Create piece ID matching the format used in TurnContent
    const pieceId = `${index}-${piece.kind}-${piece.color}`;
    return selectedPieces.some(selected => 
      selected.id === pieceId || selected === pieceId
    );
  };
  

  return (
    <div className={containerClasses}>
      <div className="piece-tray__grid">
        {pieces.map((piece, index) => {
          const isSelectable = !!onPieceClick;
          const isSelected = isPieceSelected(piece, index);
          
          // Determine variant based on animation type and selectability
          let pieceVariant = 'default';
          if (animateAppear && animationType === 'verticalDrop') {
            pieceVariant = 'dealing';
          } else if (isSelectable) {
            pieceVariant = 'selectable';
          }
          
          // Calculate animation delay based on animation type
          const delay = animateAppear ? 
            (animationType === 'verticalDrop' ? index * 0.08 : index * 0.1) : 
            undefined;
          
          return (
            <GamePiece
              key={index}
              piece={piece}
              size="large"
              variant={pieceVariant}
              selected={isSelected}
              showValue={showValues}
              onClick={isSelectable ? () => handlePieceClick(piece, index) : null}
              animationDelay={delay}
            />
          );
        })}
      </div>
    </div>
  );
};

PieceTray.propTypes = {
  pieces: PropTypes.arrayOf(PropTypes.shape({
    type: PropTypes.string,
    color: PropTypes.string,
    value: PropTypes.number
  })),
  variant: PropTypes.oneOf(['default', 'active', 'fixed']),
  onPieceClick: PropTypes.func,
  selectedPieces: PropTypes.array,
  showValues: PropTypes.bool,
  animateAppear: PropTypes.bool,
  animationType: PropTypes.oneOf(['bounce', 'verticalDrop']),
  className: PropTypes.string
};

export default PieceTray;