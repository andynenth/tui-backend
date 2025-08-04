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
    borderRadius: layout.radiusMd,
    backgroundColor: colors.white,
    border: `2px solid ${colors.gray300}`,
    transition: `all ${motion.durationBase} ${motion.easeInOut}`,
    cursor: 'pointer',
    userSelect: 'none',
    transformStyle: 'preserve-3d',
  },
  
  // Sizes
  mini: {
    width: '30px',
    height: '40px',
    fontSize: typography.textXs,
  },
  
  small: {
    width: '40px',
    height: '50px',
    fontSize: typography.textSm,
  },
  
  medium: {
    width: '50px',
    height: '65px',
    fontSize: typography.textBase,
  },
  
  large: {
    width: '60px',
    height: '80px',
    fontSize: typography.textLg,
  },
  
  // Variants
  default: {
    boxShadow: shadows.sm,
    ':hover': {
      transform: 'translateY(-2px)',
      boxShadow: shadows.md,
    },
  },
  
  table: {
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    boxShadow: shadows.md,
  },
  
  selectable: {
    cursor: 'pointer',
    ':hover': {
      borderColor: colors.primary,
      transform: 'scale(1.05)',
    },
  },
  
  dealing: {
    animation: `${flipAnimation} 0.6s ${motion.easeInOut}`,
  },
  
  // States
  selected: {
    borderColor: colors.primary,
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
    borderColor: colors.danger,
    color: colors.danger,
  },
  
  black: {
    backgroundColor: 'rgba(33, 37, 41, 0.1)',
    borderColor: colors.gray700,
    color: colors.gray800,
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
    borderRadius: layout.radiusMd,
  },
  
  faceFront: {
    transform: 'rotateY(0deg)',
  },
  
  faceBack: {
    transform: 'rotateY(180deg)',
    backgroundColor: colors.gray600,
    backgroundImage: `linear-gradient(45deg, ${colors.gray700} 25%, transparent 25%, transparent 75%, ${colors.gray700} 75%, ${colors.gray700}), linear-gradient(45deg, ${colors.gray700} 25%, transparent 25%, transparent 75%, ${colors.gray700} 75%, ${colors.gray700})`,
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
    fontWeight: typography.weightBold,
  },
  
  characterImage: {
    width: '80%',
    height: '80%',
    objectFit: 'contain',
  },
  
  value: {
    fontSize: typography.textXs,
    fontWeight: typography.weightSemibold,
    color: colors.gray600,
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
        title={className.includes('invalid-play') ? "Play type doesn't match" : ''}
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