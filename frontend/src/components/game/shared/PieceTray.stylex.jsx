import React from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, layout, shadows } from '../../../design-system/tokens.stylex';
import GamePiece from './GamePiece.stylex';

// PieceTray styles
const styles = stylex.create({
  container: {
    width: '100%',
    padding: spacing.lg,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: layout.radiusLg,
    border: `1px solid ${colors.gray200}`,
  },
  
  // Variants
  active: {
    backgroundColor: 'rgba(13, 110, 253, 0.05)',
    borderColor: colors.primary,
    boxShadow: `0 0 0 2px rgba(13, 110, 253, 0.1)`,
  },
  
  fixed: {
    backgroundColor: colors.gray50,
    borderColor: colors.gray300,
  },
  
  inner: {
    width: '100%',
    overflow: 'hidden',
  },
  
  grid: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: spacing.md,
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '100px',
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
}) => {
  // Apply container styles
  const containerProps = stylex.props(
    styles.container,
    variant === 'active' && styles.active,
    variant === 'fixed' && styles.fixed
  );

  // During migration, allow combining with existing CSS classes
  const combinedContainerProps = className 
    ? { ...containerProps, className: `${containerProps.className || ''} ${className}`.trim() }
    : containerProps;

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

  return (
    <div {...combinedContainerProps}>
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
};

export default PieceTray;