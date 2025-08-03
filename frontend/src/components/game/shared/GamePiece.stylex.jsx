// GamePiece component with StyleX
import React from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
import { useTheme } from '../../../contexts/ThemeContext';
import {
  getPieceDisplay,
  formatPieceValue,
  getThemePieceSVG,
  USE_SVG_PIECES,
} from '../../../utils/pieceMapping';
import { colors, spacing, shadows, layout, motion, typography } from '../../../design-system/tokens.stylex';

// Animation keyframes
const deal = stylex.keyframes({
  '0%': {
    transform: 'translateY(-100px) rotate(180deg)',
    opacity: 0,
  },
  '50%': {
    transform: 'translateY(-20px) rotate(90deg)',
    opacity: 0.5,
  },
  '100%': {
    transform: 'translateY(0) rotate(0deg)',
    opacity: 1,
  },
});

const pieceSelect = stylex.keyframes({
  '0%': {
    transform: 'scale(1)',
  },
  '50%': {
    transform: 'scale(1.1)',
  },
  '100%': {
    transform: 'scale(1.05)',
  },
});

const flip = stylex.keyframes({
  '0%': {
    transform: 'rotateY(0)',
  },
  '100%': {
    transform: 'rotateY(180deg)',
  },
});

const pulse = stylex.keyframes({
  '0%, 100%': {
    transform: 'scale(1)',
    boxShadow: shadows.piece,
  },
  '50%': {
    transform: 'scale(1.05)',
    boxShadow: shadows.pieceGlow,
  },
});

const styles = stylex.create({
  piece: {
    position: 'relative',
    borderRadius: layout.radiusMd,
    cursor: 'pointer',
    transition: motion.transitionBase,
    transformStyle: 'preserve-3d',
    userSelect: 'none',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    boxShadow: shadows.piece,
    
    ':hover': {
      transform: 'translateY(-4px)',
      boxShadow: shadows.pieceHover,
    },
  },
  
  // Size variants
  sizeMini: {
    width: '40px',
    height: '50px',
    fontSize: typography.textXs,
  },
  
  sizeSmall: {
    width: '50px',
    height: '65px',
    fontSize: typography.textSm,
  },
  
  sizeMedium: {
    width: '60px',
    height: '80px',
    fontSize: typography.textMd,
  },
  
  sizeLarge: {
    width: '70px',
    height: '95px',
    fontSize: typography.textLg,
  },
  
  // Variant styles
  variantDefault: {
    backgroundColor: colors.surface,
  },
  
  variantTable: {
    backgroundColor: colors.surfaceHover,
    border: `2px solid ${colors.border}`,
  },
  
  variantSelectable: {
    cursor: 'pointer',
    transition: `all ${motion.durationFast} ${motion.easeInOut}`,
    
    ':hover': {
      transform: 'translateY(-4px) scale(1.05)',
      boxShadow: shadows.glow,
    },
  },
  
  variantDealing: {
    animation: `${deal} 0.5s ${motion.easeOut}`,
    animationFillMode: 'both',
  },
  
  // Selected state
  selected: {
    transform: 'scale(1.05)',
    boxShadow: shadows.pieceGlow,
    animation: `${pieceSelect} 0.2s ${motion.easeOut}`,
    border: `3px solid ${colors.primary}`,
    
    ':hover': {
      transform: 'scale(1.08)',
    },
  },
  
  // Color variants
  colorRed: {
    backgroundColor: colors.pieceRed,
    backgroundImage: 'linear-gradient(135deg, rgba(255,255,255,0.2) 0%, transparent 50%)',
    color: colors.textLight,
  },
  
  colorBlack: {
    backgroundColor: colors.pieceBlack,
    backgroundImage: 'linear-gradient(135deg, rgba(255,255,255,0.1) 0%, transparent 50%)',
    color: colors.textLight,
  },
  
  colorGold: {
    backgroundColor: colors.pieceGold,
    backgroundImage: 'linear-gradient(135deg, rgba(255,255,255,0.3) 0%, transparent 50%)',
    color: colors.textDark,
    boxShadow: shadows.pieceGlow,
  },
  
  colorSilver: {
    backgroundColor: colors.pieceSilver,
    backgroundImage: 'linear-gradient(135deg, rgba(255,255,255,0.2) 0%, transparent 50%)',
    color: colors.textDark,
  },
  
  // Flippable piece styles
  flippable: {
    transformStyle: 'preserve-3d',
    perspective: '1000px',
  },
  
  flipped: {
    animation: `${flip} 0.6s ${motion.easeInOut}`,
    transform: 'rotateY(180deg)',
  },
  
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
    backgroundColor: colors.surface,
    backgroundImage: `linear-gradient(45deg, ${colors.surfaceHover} 25%, transparent 25%, transparent 75%, ${colors.surfaceHover} 75%, ${colors.surfaceHover}), linear-gradient(45deg, ${colors.surfaceHover} 25%, transparent 25%, transparent 75%, ${colors.surfaceHover} 75%, ${colors.surfaceHover})`,
    backgroundSize: '10px 10px',
    backgroundPosition: '0 0, 5px 5px',
    border: `2px solid ${colors.border}`,
  },
  
  character: {
    fontSize: '1.5em',
    fontWeight: typography.weightBold,
    textAlign: 'center',
    lineHeight: '1',
    marginBottom: spacing.xs,
  },
  
  characterImage: {
    width: '80%',
    height: 'auto',
    objectFit: 'contain',
  },
  
  value: {
    fontSize: typography.textXs,
    fontWeight: typography.weightMedium,
    backgroundColor: 'rgba(0, 0, 0, 0.2)',
    color: colors.textLight,
    padding: '2px 6px',
    borderRadius: layout.radiusSm,
    marginTop: spacing.xs,
  },
  
  // Invalid play indicator
  invalid: {
    opacity: 0.5,
    filter: 'grayscale(50%)',
    cursor: 'not-allowed',
    
    ':hover': {
      transform: 'none',
      boxShadow: shadows.piece,
    },
  },
  
  // Pulse animation for special pieces
  pulsing: {
    animation: `${pulse} 2s ${motion.easeInOut} infinite`,
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
  
  // Get color style based on piece
  const getColorStyle = () => {
    if (!piece?.color) return null;
    const colorMap = {
      'red': styles.colorRed,
      'RED': styles.colorRed,
      'black': styles.colorBlack,
      'BLACK': styles.colorBlack,
      'gold': styles.colorGold,
      'GOLD': styles.colorGold,
      'silver': styles.colorSilver,
      'SILVER': styles.colorSilver,
    };
    return colorMap[piece.color] || null;
  };
  
  // Get size style
  const getSizeStyle = () => {
    const sizeMap = {
      'mini': styles.sizeMini,
      'small': styles.sizeSmall,
      'medium': styles.sizeMedium,
      'large': styles.sizeLarge,
    };
    return sizeMap[size] || styles.sizeMedium;
  };
  
  // Get variant style
  const getVariantStyle = () => {
    const variantMap = {
      'default': styles.variantDefault,
      'table': styles.variantTable,
      'selectable': styles.variantSelectable,
      'dealing': styles.variantDealing,
    };
    return variantMap[variant] || styles.variantDefault;
  };
  
  // Custom animation delay
  const customStyle = animationDelay !== undefined ? {
    animationDelay: `${animationDelay}s`,
  } : {};
  
  // Check if piece is invalid
  const isInvalid = className.includes('invalid-play');
  
  // Render flippable piece with front/back faces
  if (flippable) {
    return (
      <div
        {...stylex.props(
          styles.piece,
          getSizeStyle(),
          getVariantStyle(),
          styles.flippable,
          flipped && styles.flipped,
          selected && styles.selected,
          isInvalid && styles.invalid,
          className && { className }
        )}
        onClick={onClick}
        style={customStyle}
        title={isInvalid ? "Play type doesn't match" : ''}
      >
        <div {...stylex.props(styles.face, styles.faceBack)} />
        <div {...stylex.props(
          styles.face,
          styles.faceFront,
          getColorStyle()
        )}>
          {USE_SVG_PIECES ? (
            <img
              {...stylex.props(styles.characterImage)}
              src={getThemePieceSVG(piece, currentTheme)}
              alt={getPieceDisplay(piece)}
            />
          ) : (
            <div {...stylex.props(styles.character)}>
              {getPieceDisplay(piece)}
            </div>
          )}
        </div>
      </div>
    );
  }
  
  // Render default/selectable variants
  return (
    <div
      {...stylex.props(
        styles.piece,
        getSizeStyle(),
        getVariantStyle(),
        getColorStyle(),
        selected && styles.selected,
        isInvalid && styles.invalid,
        piece?.value > 10 && styles.pulsing,
        className && { className }
      )}
      onClick={onClick}
      style={customStyle}
      title={isInvalid ? "Play type doesn't match" : ''}
    >
      <div {...stylex.props(styles.character)}>
        {USE_SVG_PIECES ? (
          <img
            {...stylex.props(styles.characterImage)}
            src={getThemePieceSVG(piece, currentTheme)}
            alt={getPieceDisplay(piece)}
          />
        ) : (
          getPieceDisplay(piece)
        )}
      </div>
      {showValue && (
        <div {...stylex.props(styles.value)}>
          {formatPieceValue(piece)}
        </div>
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