// PieceTray component with StyleX
import React from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
import GamePiece from './GamePiece.stylex';
import { colors, spacing, shadows, layout, motion, typography } from '../../../design-system/tokens.stylex';

const styles = stylex.create({
  container: {
    position: 'relative',
    width: '100%',
    padding: spacing.md,
    backgroundColor: 'transparent',
    borderRadius: layout.radiusLg,
    transition: motion.transitionBase,
  },
  
  // Variant styles
  variantDefault: {
    backgroundColor: 'rgba(0, 0, 0, 0.05)',
  },
  
  variantActive: {
    backgroundColor: colors.surface,
    boxShadow: shadows.md,
    border: `2px solid ${colors.primary}`,
    animation: 'pulse 2s infinite',
  },
  
  variantFixed: {
    backgroundColor: colors.surfaceHover,
    boxShadow: shadows.lg,
    border: `1px solid ${colors.border}`,
  },
  
  inner: {
    position: 'relative',
    width: '100%',
    minHeight: '100px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(70px, 1fr))',
    gap: spacing.sm,
    width: '100%',
    maxWidth: '600px',
    alignItems: 'center',
    justifyContent: 'center',
    
    '@media (max-width: 640px)': {
      gridTemplateColumns: 'repeat(auto-fit, minmax(60px, 1fr))',
      gap: spacing.xs,
    },
  },
  
  // Empty state
  emptyState: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.xl,
    color: colors.gray500,
    fontSize: typography.textMd,
    fontStyle: 'italic',
    minHeight: '120px',
  },
  
  emptyIcon: {
    fontSize: '2rem',
    marginBottom: spacing.sm,
    opacity: 0.5,
  },
  
  // Loading state
  loadingContainer: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '120px',
    gap: spacing.md,
  },
  
  loadingDot: {
    width: '12px',
    height: '12px',
    backgroundColor: colors.primary,
    borderRadius: layout.radiusFull,
    animation: 'bounce 1.4s ease-in-out infinite',
  },
  
  loadingDot1: {
    animationDelay: '-0.32s',
  },
  
  loadingDot2: {
    animationDelay: '-0.16s',
  },
  
  loadingDot3: {
    animationDelay: '0s',
  },
  
  // Labels
  label: {
    position: 'absolute',
    top: '-10px',
    left: spacing.md,
    backgroundColor: colors.surface,
    padding: `${spacing.xs} ${spacing.sm}`,
    borderRadius: layout.radiusSm,
    fontSize: typography.textSm,
    fontWeight: typography.weightMedium,
    color: colors.gray700,
    boxShadow: shadows.sm,
    zIndex: 1,
  },
  
  // Animation container for staggered appearance
  animationContainer: {
    animation: 'fadeInUp 0.4s ease-out',
    animationFillMode: 'both',
  },
});

const PieceTray = ({
  pieces = [],
  variant = 'default',
  onPieceClick,
  selectedPieces = [],
  showValues = true,
  animateAppear = false,
  animationType = 'bounce',
  className = '',
  label = '',
  loading = false,
  emptyMessage = 'No pieces available',
}) => {
  // Get variant style
  const getVariantStyle = () => {
    const variantMap = {
      'default': styles.variantDefault,
      'active': styles.variantActive,
      'fixed': styles.variantFixed,
    };
    return variantMap[variant] || styles.variantDefault;
  };
  
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
    return selectedPieces.some(
      (selected) => selected.id === pieceId || selected === pieceId
    );
  };
  
  // Render loading state
  if (loading) {
    return (
      <div {...stylex.props(
        styles.container,
        getVariantStyle(),
        className && { className }
      )}>
        <div {...stylex.props(styles.inner)}>
          <div {...stylex.props(styles.loadingContainer)}>
            <div {...stylex.props(styles.loadingDot, styles.loadingDot1)} />
            <div {...stylex.props(styles.loadingDot, styles.loadingDot2)} />
            <div {...stylex.props(styles.loadingDot, styles.loadingDot3)} />
          </div>
        </div>
      </div>
    );
  }
  
  // Render empty state
  if (!pieces || pieces.length === 0) {
    return (
      <div {...stylex.props(
        styles.container,
        getVariantStyle(),
        className && { className }
      )}>
        {label && (
          <div {...stylex.props(styles.label)}>
            {label}
          </div>
        )}
        <div {...stylex.props(styles.inner)}>
          <div {...stylex.props(styles.emptyState)}>
            <div {...stylex.props(styles.emptyIcon)}>🎲</div>
            <div>{emptyMessage}</div>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div {...stylex.props(
      styles.container,
      getVariantStyle(),
      animateAppear && styles.animationContainer,
      className && { className }
    )}>
      {label && (
        <div {...stylex.props(styles.label)}>
          {label}
        </div>
      )}
      <div {...stylex.props(styles.inner)}>
        <div {...stylex.props(styles.grid)}>
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
            const delay = animateAppear
              ? animationType === 'verticalDrop'
                ? index * 0.08
                : index * 0.1
              : undefined;
            
            return (
              <GamePiece
                key={index}
                piece={piece}
                size="large"
                variant={pieceVariant}
                selected={isSelected}
                showValue={showValues}
                onClick={
                  isSelectable ? () => handlePieceClick(piece, index) : null
                }
                animationDelay={delay}
              />
            );
          })}
        </div>
      </div>
    </div>
  );
};

PieceTray.propTypes = {
  pieces: PropTypes.arrayOf(
    PropTypes.shape({
      type: PropTypes.string,
      kind: PropTypes.string,
      color: PropTypes.string,
      value: PropTypes.number,
    })
  ),
  variant: PropTypes.oneOf(['default', 'active', 'fixed']),
  onPieceClick: PropTypes.func,
  selectedPieces: PropTypes.array,
  showValues: PropTypes.bool,
  animateAppear: PropTypes.bool,
  animationType: PropTypes.oneOf(['bounce', 'verticalDrop']),
  className: PropTypes.string,
  label: PropTypes.string,
  loading: PropTypes.bool,
  emptyMessage: PropTypes.string,
};

export default PieceTray;