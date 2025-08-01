import React from 'react';
import PropTypes from 'prop-types';
import { useTheme } from '../../../contexts/ThemeContext';
import {
  getPieceDisplay,
  getPieceColorClass,
  formatPieceValue,
  getPieceSVG,
  getThemePieceSVG,
  USE_SVG_PIECES,
} from '../../../utils/pieceMapping';

/**
 * GamePiece Component
 *
 * A unified component for rendering game pieces across all phases.
 * Supports different sizes, variants, and states.
 *
 * @param {Object} piece - The piece data containing type, color, and value
 * @param {string} size - Piece size: 'mini', 'small', 'medium', 'large' (default: 'medium')
 * @param {string} variant - Display variant: 'default', 'table', 'selectable' (default: 'default')
 * @param {boolean} selected - Whether the piece is selected (for selectable variant)
 * @param {boolean} flipped - Whether the piece is flipped (for flippable pieces)
 * @param {boolean} flippable - Whether the piece can be flipped (shows front/back faces)
 * @param {boolean} showValue - Whether to show the piece value/points
 * @param {function} onClick - Click handler function
 * @param {string} className - Additional CSS classes
 * @param {number} animationDelay - Animation delay in seconds for staggered effects
 */
const GamePiece = ({
  piece,
  size = 'medium',
  variant = 'default',
  selected = false,
  flipped = false,
  flippable = false,
  showValue = false,
  onClick,
  className = '',
  animationDelay,
}) => {
  const { currentTheme } = useTheme();
  
  // DEBUG: Log GamePiece render data
  console.log('GamePiece rendering:', {
    piece,
    currentTheme: currentTheme ? { id: currentTheme.id, name: currentTheme.name } : null,
    USE_SVG_PIECES
  });
  // Build class names
  const classes = [
    'game-piece',
    `game-piece--${size}`,
    `game-piece--${variant}`,
    getPieceColorClass(piece),
    selected && 'selected',
    flippable && 'flippable',
    flipped && 'flipped',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  // Build style object
  const style = {};
  if (animationDelay !== undefined) {
    style.animationDelay = `${animationDelay}s`;
  }

  // Render flippable piece with front/back faces
  if (flippable) {
    return (
      <div
        className={classes}
        onClick={onClick}
        style={style}
        title={
          className.includes('invalid-play') ? "Play type doesn't match" : ''
        }
      >
        <div className="game-piece__face game-piece__face--back"></div>
        <div
          className={`game-piece__face game-piece__face--front ${getPieceColorClass(piece)}`}
        >
          {(() => {
            const svgAsset = USE_SVG_PIECES ? getThemePieceSVG(piece, currentTheme) : null;
            return USE_SVG_PIECES && svgAsset ? (
              <>
                <img
                  src={svgAsset}
                  alt={getPieceDisplay(piece)}
                  onError={(e) => {
                    console.error('GamePiece: Flippable SVG failed to load, falling back to text:', {
                      piece,
                      svgAsset,
                      errorEvent: e
                    });
                    e.target.style.display = 'none';
                    e.target.nextSibling.style.display = 'block';
                  }}
                />
                <span style={{ display: 'none' }}>
                  {getPieceDisplay(piece)}
                </span>
              </>
            ) : (
              getPieceDisplay(piece)
            );
          })()}
        </div>
      </div>
    );
  }

  // Render default/selectable variants
  const svgAsset = USE_SVG_PIECES ? getThemePieceSVG(piece, currentTheme) : null;
  
  return (
    <div className={classes} onClick={onClick} style={style}>
      <div className="game-piece__character">
        {USE_SVG_PIECES && svgAsset ? (
          <img
            src={svgAsset}
            alt={getPieceDisplay(piece)}
            onError={(e) => {
              console.error('GamePiece: SVG failed to load, falling back to text:', {
                piece,
                svgAsset,
                errorEvent: e
              });
              // Hide the broken image and show fallback text
              e.target.style.display = 'none';
              e.target.nextSibling.style.display = 'block';
            }}
          />
        ) : null}
        <span style={{ display: (USE_SVG_PIECES && svgAsset) ? 'none' : 'block' }}>
          {getPieceDisplay(piece)}
        </span>
      </div>
      {showValue && (
        <div className="game-piece__value">{formatPieceValue(piece)}</div>
      )}
    </div>
  );
};

GamePiece.propTypes = {
  piece: PropTypes.shape({
    kind: PropTypes.string,
    color: PropTypes.string,
    value: PropTypes.number,
  }).isRequired,
  size: PropTypes.oneOf(['mini', 'small', 'medium', 'large']),
  variant: PropTypes.oneOf(['default', 'table', 'selectable', 'dealing']),
  selected: PropTypes.bool,
  flipped: PropTypes.bool,
  flippable: PropTypes.bool,
  showValue: PropTypes.bool,
  onClick: PropTypes.func,
  className: PropTypes.string,
  animationDelay: PropTypes.number,
};

export default GamePiece;
