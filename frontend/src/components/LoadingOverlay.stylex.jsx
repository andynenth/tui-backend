import React from 'react';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, motion, shadows, layout } from '../design-system/tokens.stylex';
import { animations } from '../design-system/utils.stylex';

// Spinner animations
const spinAnimation = stylex.keyframes({
  '0%': {
    transform: 'rotate(0deg)',
  },
  '100%': {
    transform: 'rotate(360deg)',
  },
});

const spinReverseAnimation = stylex.keyframes({
  '0%': {
    transform: 'rotate(0deg)',
  },
  '100%': {
    transform: 'rotate(-360deg)',
  },
});

// LoadingOverlay styles
const styles = stylex.create({
  overlay: {
    position: 'fixed',
    top: 0,
    right: 0,
    bottom: 0,
    left: 0,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    backdropFilter: 'blur(4px)',
    zIndex: 50,
    animation: `${animations.fadeIn} ${motion.durationBase} ${motion.easeOut}`,
  },
  
  overlayLight: {
    position: 'absolute',
    top: 0,
    right: 0,
    bottom: 0,
    left: 0,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    zIndex: 10,
    animation: `${animations.fadeIn} ${motion.durationBase} ${motion.easeOut}`,
  },
  
  card: {
    backgroundColor: colors.white,
    borderRadius: layout.radiusXl,
    boxShadow: shadows.xl,
    padding: spacing.xxxl,
    maxWidth: '24rem',
    width: '100%',
    margin: spacing.lg,
    animation: `${animations.scaleIn} ${motion.durationBase} ${motion.easeOut} 100ms`,
  },
  
  content: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: spacing.lg,
  },
  
  spinnerContainer: {
    position: 'relative',
    width: '48px',
    height: '48px',
  },
  
  spinner: {
    width: '48px',
    height: '48px',
    border: `4px solid ${colors.gray200}`,
    borderTopColor: colors.primary,
    borderRadius: layout.radiusFull,
    animation: `${spinAnimation} 1s linear infinite`,
  },
  
  spinnerOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    width: '48px',
    height: '48px',
    border: '4px solid transparent',
    borderLeftColor: 'rgba(13, 110, 253, 0.5)',
    borderRadius: layout.radiusFull,
    animation: `${spinReverseAnimation} 1.5s linear infinite`,
  },
  
  textContainer: {
    textAlign: 'center',
    animation: `${animations.slideIn} ${motion.durationSlow} ${motion.easeOut} 200ms`,
  },
  
  message: {
    fontSize: typography.textLg,
    fontWeight: typography.weightMedium,
    color: colors.gray800,
    marginBottom: spacing.xs,
  },
  
  subtitle: {
    fontSize: typography.textSm,
    color: colors.gray500,
  },
});

const LoadingOverlay = ({
  isVisible = false,
  message = 'Loading...',
  subtitle = '',
  showSpinner = true,
  overlay = true,
  className = '',
}) => {
  if (!isVisible) return null;

  // Apply overlay styles
  const overlayProps = stylex.props(
    overlay ? styles.overlay : styles.overlayLight
  );

  // During migration, allow combining with existing CSS classes
  const combinedOverlayProps = className 
    ? { ...overlayProps, className: `${overlayProps.className || ''} ${className}`.trim() }
    : overlayProps;

  return (
    <div {...combinedOverlayProps}>
      <div {...stylex.props(styles.card)}>
        <div {...stylex.props(styles.content)}>
          {/* Enhanced Spinner */}
          {showSpinner && (
            <div {...stylex.props(styles.spinnerContainer)}>
              <div {...stylex.props(styles.spinner)} />
              <div {...stylex.props(styles.spinnerOverlay)} />
            </div>
          )}

          {/* Message */}
          <div {...stylex.props(styles.textContainer)}>
            <h3 {...stylex.props(styles.message)}>
              {message}
            </h3>

            {subtitle && (
              <p {...stylex.props(styles.subtitle)}>{subtitle}</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoadingOverlay;