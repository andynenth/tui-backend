import React from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
// Token values must be inlined for StyleX compilation
// import { colors, spacing, typography, motion, shadows, layout } from '../../../utils/pieceUtils';
import { useTheme } from '../../../contexts/ThemeContext';
import {
  getPieceDisplay,
  getPieceColorClass,
  formatPieceValue,
  getPieceSVG,
  getThemePieceSVG,
  USE_SVG_PIECES,
} from '../../../utils/pieceUtils';

// Define flip animation
const flipAnimation = stylex.keyframes({
  '0%': {
    transform: 'rotate(0deg)',
  },
  '100%': {
    transform: 'rotate(360deg)',
  },
});

// Game piece styles
const styles = stylex.create({
  piece: {
    position: 'relative',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: '8px',
    backgroundColor: '#ffffff',
    borderWidth: '2px',
    borderStyle: 'solid',
    borderColor: '#dee2e6',
    transition: 'all 150ms cubic-bezier(0.4, 0, 0.2, 1)',
    cursor: 'pointer',
    userSelect: 'none',
    transformStyle: 'preserve-3d',
  },
  
  // Sizes
  mini: {
    width: '30px',
    height: '40px',
    fontSize: '10px',
  },
  
  small: {
    width: '40px',
    height: '50px',
    fontSize: '12px',
  },
  
  medium: {
    width: '50px',
    height: '40px',
    fontSize: '16px',
  },
  
  large: {
    width: '40px',
    height: '80px',
    fontSize: '12px',
  },
  
  // Variants
  default: {
    boxShadow: '0 2px 6px rgba(0, 0, 0, 0.04)',
    ':hover': {
      transform: 'translateY(-2px)',
      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)',
    },
  },
  
  table: {
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)',
  },
  
  selectable: {
    cursor: 'pointer',
    ':hover': {
      borderColor: '#dee2e6',
      transform: 'scale(1.05)',
    },
  },
  
  dealing: {
    animationName: flipAnimation,
    animationDuration: '0.5s',
    animationTimingFunction: 'cubic-bezier(0.4, 0, 0.2, 1)',
    backgroundColor: 'rgba(13, 110, 253, 0.1)',
    transform: 'rotate(5deg)',
    boxShadow: '0 0 0 3px rgba(13, 110, 253, 0.2)',
  },
  
  flippable: {
    transformStyle: 'preserve-3d',
    perspective: '1000px',
  },
  
  flipped: {
    transform: 'rotate(5deg)',
  },
  
  // Piece colors
  red: {
    backgroundColor: 'rgba(220, 53, 69, 0.1)',
    borderColor: '#dee2e6',
    color: '#dc3545',
  },
  
  black: {
    backgroundColor: 'rgba(33, 37, 41, 0.1)',
    borderColor: '#dee2e6',
    color: '#212529',
  },
  
  // Piece face (for flippable pieces)
  face: {
    position: 'relative',
    width: '40px',
    height: '40px',
    backfaceVisibility: 'hidden',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: '10px',
  },
  
  faceFront: {
    transform: 'rotate(5deg)',
  },
  
  faceBack: {
    transform: 'rotateY(180deg)',
    backgroundColor: '#343a40',
    backgroundImage: 'linear-gradient(45deg, #343a40 25%, transparent 25%, transparent 75%, #343a40 75%, #343a40)',
    backgroundSize: '10px 10px',
    backgroundPosition: '0 0',
  },
  
  // Content elements
  character: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flex: 1,
    width: '40px',
    fontWeight: '700',
  },
  
  characterImage: {
    width: '80%',
    height: '40px',
    objectFit: 'contain',
  },
  
  value: {
    fontSize: '14px',
    fontWeight: '600',
    color: '#6c757d',
    marginTop: '2px',
  },
});

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
  
  // Get piece color style
  const getPieceColorStyle = () => {
    if (piece?.color === 'RED') return styles.red;
    if (piece?.color === 'BLACK') return styles.black;
    return null;
  };

  // Build style object for animation delay
  const inlineStyle = {};
  if (animationDelay !== undefined) {
    inlineStyle.animationDelay = animationDelay + 'ms';
  }

  // Apply piece styles
  const pieceProps = stylex.props(
    styles.piece,
    styles[size],
    styles[variant],
    selected && styles.selected,
    flippable && styles.flippable,
    flipped && styles.flipped,
    getPieceColorStyle()
  );

  // During migration, allow combining with existing CSS classes
  const combinedPieceProps = className 
    ? { 
        ...pieceProps, 
        className: (pieceProps.className + ' ' + className).trim(),
        style: { ...pieceProps.style, ...inlineStyle }
      }
    : { ...pieceProps, style: { ...pieceProps.style, ...inlineStyle } };

  // Render flippable piece with front/back faces
  if (flippable) {
    return (
      <div
        {...combinedPieceProps}
        onClick={onClick}
        title={className.includes('invalid-play') ? "Play type doesn't match" : '}
      >
        <div {...stylex.props(styles.face, styles.faceBack)} />
        <div {...stylex.props(styles.face, styles.faceFront, getPieceColorStyle())}>
          {USE_SVG_PIECES ? (
            <img
              src={getThemePieceSVG(piece, currentTheme)}
              alt={getPieceDisplay(piece)}
              {...stylex.props(styles.characterImage)}
            />
          ) : (
            getPieceDisplay(piece)
          )}
        </div>
      </div>
    );
  }

  // Render default/selectable variants
  return (
    <div {...combinedPieceProps} onClick={onClick}>
      <div {...stylex.props(styles.character)}>
        {USE_SVG_PIECES ? (
          <img
            src={getThemePieceSVG(piece, currentTheme)}
            alt={getPieceDisplay(piece)}
            {...stylex.props(styles.characterImage)}
          />
        ) : (
          getPieceDisplay(piece)
        )}
      </div>
      {showValue && (
        <div {...stylex.props(styles.value)}>{formatPieceValue(piece)}</div>
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