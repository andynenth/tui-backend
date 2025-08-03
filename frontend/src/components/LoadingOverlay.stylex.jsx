// LoadingOverlay component with StyleX
import React from 'react';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, motion, shadows, layout, backdrop } from '../design-system/tokens.stylex';

// Animation keyframes
const fadeIn = stylex.keyframes({
  '0%': {
    opacity: 0,
  },
  '100%': {
    opacity: 1,
  },
});

const zoomIn = stylex.keyframes({
  '0%': {
    opacity: 0,
    transform: 'scale(0.95)',
  },
  '100%': {
    opacity: 1,
    transform: 'scale(1)',
  },
});

const slideUp = stylex.keyframes({
  '0%': {
    opacity: 0,
    transform: 'translateY(16px)',
  },
  '100%': {
    opacity: 1,
    transform: 'translateY(0)',
  },
});

const spin = stylex.keyframes({
  '0%': {
    transform: 'rotate(0deg)',
  },
  '100%': {
    transform: 'rotate(360deg)',
  },
});

const spinReverse = stylex.keyframes({
  '0%': {
    transform: 'rotate(0deg)',
  },
  '100%': {
    transform: 'rotate(-360deg)',
  },
});

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
    zIndex: layout.zModal,
    animation: `${fadeIn} ${motion.durationNormal} ${motion.easeOut}`,
  },
  
  overlayDark: {
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    backdropFilter: `blur(${backdrop.blurSm})`,
  },
  
  overlayLight: {
    position: 'absolute',
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    zIndex: layout.zDropdown,
  },
  
  container: {
    backgroundColor: colors.textLight,
    borderRadius: layout.radiusXl,
    boxShadow: shadows.xxl,
    padding: spacing.xl,
    maxWidth: '24rem',
    width: '100%',
    margin: spacing.md,
    transformOrigin: 'center',
    animation: `${zoomIn} ${motion.durationNormal} ${motion.easeOut} 100ms`,
  },
  
  content: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: spacing.md,
  },
  
  spinnerContainer: {
    position: 'relative',
    width: '48px',
    height: '48px',
  },
  
  spinner: {
    position: 'absolute',
    width: '48px',
    height: '48px',
    border: `4px solid ${colors.gray200}`,
    borderTopColor: colors.primary,
    borderRadius: layout.radiusFull,
    animation: `${spin} 1s linear infinite`,
  },
  
  spinnerInner: {
    position: 'absolute',
    inset: 0,
    width: '48px',
    height: '48px',
    border: '4px solid transparent',
    borderLeftColor: colors.primaryHover,
    borderRadius: layout.radiusFull,
    animation: `${spinReverse} 1.5s linear infinite`,
  },
  
  textContainer: {
    textAlign: 'center',
    animation: `${slideUp} ${motion.durationSlow} ${motion.easeOut} 200ms`,
    animationFillMode: 'both',
  },
  
  message: {
    fontSize: typography.textLg,
    fontWeight: typography.weightMedium,
    color: colors.gray900,
    marginBottom: spacing.xs,
    lineHeight: typography.lineHeightNormal,
  },
  
  subtitle: {
    fontSize: typography.textSm,
    color: colors.gray500,
    lineHeight: typography.lineHeightNormal,
  },
  
  // Variations
  smallContainer: {
    padding: spacing.md,
    maxWidth: '20rem',
  },
  
  largeContainer: {
    padding: spacing.xxl,
    maxWidth: '32rem',
  },
  
  // Alternative spinner styles
  pulseSpinner: {
    width: '48px',
    height: '48px',
    backgroundColor: colors.primary,
    borderRadius: layout.radiusFull,
    animation: 'pulse 1.5s ease-in-out infinite',
  },
  
  dotsContainer: {
    display: 'flex',
    gap: spacing.xs,
  },
  
  dot: {
    width: '12px',
    height: '12px',
    backgroundColor: colors.primary,
    borderRadius: layout.radiusFull,
    animation: 'bounce 1.4s ease-in-out infinite',
  },
  
  dot1: {
    animationDelay: '-0.32s',
  },
  
  dot2: {
    animationDelay: '-0.16s',
  },
  
  dot3: {
    animationDelay: '0s',
  },
});

const LoadingOverlay = ({
  isVisible = false,
  message = 'Loading...',
  subtitle = '',
  showSpinner = true,
  overlay = true,
  className = '',
  size = 'medium',
  spinnerType = 'dual',
}) => {
  if (!isVisible) return null;

  // Size variations
  const sizeStyle = {
    small: styles.smallContainer,
    medium: styles.container,
    large: styles.largeContainer,
  }[size] || styles.container;

  // Render different spinner types
  const renderSpinner = () => {
    if (!showSpinner) return null;

    switch (spinnerType) {
      case 'dots':
        return (
          <div {...stylex.props(styles.dotsContainer)}>
            <div {...stylex.props(styles.dot, styles.dot1)} />
            <div {...stylex.props(styles.dot, styles.dot2)} />
            <div {...stylex.props(styles.dot, styles.dot3)} />
          </div>
        );
      
      case 'pulse':
        return (
          <div {...stylex.props(styles.pulseSpinner)} />
        );
      
      case 'dual':
      default:
        return (
          <div {...stylex.props(styles.spinnerContainer)}>
            <div {...stylex.props(styles.spinner)} />
            <div {...stylex.props(styles.spinnerInner)} />
          </div>
        );
    }
  };

  return (
    <div
      {...stylex.props(
        styles.overlay,
        overlay ? styles.overlayDark : styles.overlayLight,
        // Allow className for migration period
        className && { className }
      )}
    >
      <div {...stylex.props(sizeStyle)}>
        <div {...stylex.props(styles.content)}>
          {/* Spinner */}
          {renderSpinner()}

          {/* Message */}
          <div {...stylex.props(styles.textContainer)}>
            <h3 {...stylex.props(styles.message)}>
              {message}
            </h3>

            {subtitle && (
              <p {...stylex.props(styles.subtitle)}>
                {subtitle}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoadingOverlay;