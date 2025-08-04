import React from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, motion, shadows, layout } from '../../../design-system/tokens.stylex';
import { useTheme } from '../../../contexts/ThemeContext';
import {
  getPieceDisplay,
  getPieceColorClass,
  formatPieceValue,
  getPieceSVG,
  getThemePieceSVG,
  USE_SVG_PIECES,
} from '../../../utils/pieceMapping';

// Define flip animation
const flipAnimation = stylex.keyframes({
  '0%': {
    transform: 'rotateY(0deg)',
  },
  '100%': {
    transform: 'rotateY(180deg)',
  },
});

// Game piece styles
const styles = stylex.create({
  piece: {
    position: 'relative',
    display: 'inline-flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: '0.375rem',
    backgroundColor: '#ffffff',
    borderWidth: '2px',
    borderStyle: 'solid',
    borderColor: '#dee2e6',
    transition: `all '300ms' 'cubic-bezier(0.4, 0, 0.2, 1)'`,
    cursor: 'pointer',
    userSelect: 'none',
    transformStyle: 'preserve-3d',
  },
  
  // Sizes
  mini: {
    width: '30px',
    height: '40px',
    fontSize: '0.75rem',
  },
  
  small: {
    width: '40px',
    height: '50px',
    fontSize: '0.875rem',
  },
  
  medium: {
    width: '50px',
    height: '65px',
    fontSize: '1rem',
  },
  
  large: {
    width: '60px',
    height: '80px',
    fontSize: '1.125rem',
  },
  
  // Variants
  default: {
    boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    ':hover': {
      transform: 'translateY(-2px)',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    },
  },
  
  table: {
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  },
  
  selectable: {
    cursor: 'pointer',
    ':hover': {
      borderColor: '#0d6efd',
      transform: 'scale(1.05)',
    },
  },
  
  dealing: {
    animation: `${flipAnimation} 0.6s 'cubic-bezier(0.4, 0, 0.2, 1)'`,
  },
  
  // States
  selected: {
    borderColor: '#0d6efd',
    backgroundColor: 'rgba(13, 110, 253, 0.1)',
    transform: 'scale(1.1)',
    boxShadow: `0 0 0 3px rgba(13, 110, 253, 0.2)`,
  },
  
  flippable: {
    transformStyle: 'preserve-3d',
    perspective: '1000px',
  },
  
  flipped: {
    transform: 'rotateY(180deg)',
  },
  
  // Piece colors
  red: {
    backgroundColor: 'rgba(220, 53, 69, 0.1)',
    borderColor: '#dc3545',
    color: '#dc3545',
  },
  
  black: {
    backgroundColor: 'rgba(33, 37, 41, 0.1)',
    borderColor: '#495057',
    color: '#343a40',
  },
  
  // Piece face (for flippable pieces)
  face: {
    position: 'absolute',
    width: '100%',
    height: '100%',
    backfaceVisibility: 'hidden',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: '0.375rem',
  },
  
  faceFront: {
    transform: 'rotateY(0deg)',
  },
  
  faceBack: {
    transform: 'rotateY(180deg)',
    backgroundColor: '#6c757d',
    backgroundImage: `linear-gradient(45deg, '#495057' 25%, transparent 25%, transparent 75%, '#495057' 75%, '#495057'), linear-gradient(45deg, '#495057' 25%, transparent 25%, transparent 75%, '#495057' 75%, '#495057')`,
    backgroundSize: '10px 10px',
    backgroundPosition: '0 0, 5px 5px',
  },
  
  // Content elements
  character: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flex: 1,
    width: '100%',
    fontWeight: '700',
  },
  
  characterImage: {
    width: '80%',
    height: '80%',
    objectFit: 'contain',
  },
  
  value: {
    fontSize: '0.75rem',
    fontWeight: '600',
    color: '#6c757d',
    marginTop: spacing.xxs,
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
    inlineStyle.animationDelay = `${animationDelay}s`;
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
        className: `${pieceProps.className || ''} ${className}`.trim(),
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