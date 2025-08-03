import React, { memo } from 'react';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, motion, shadows, layout, gradients } from '../design-system/tokens.stylex';

// Animation keyframes
const spin = stylex.keyframes({
  '0%': {
    transform: 'rotate(0deg)',
  },
  '100%': {
    transform: 'rotate(360deg)',
  },
});

const scaleDown = stylex.keyframes({
  '0%': {
    transform: 'scale(1)',
  },
  '100%': {
    transform: 'scale(0.95)',
  },
});

// Button styles
const styles = stylex.create({
  base: {
    // Reset
    border: 'none',
    background: 'none',
    font: 'inherit',
    cursor: 'pointer',
    outline: 'none',
    userSelect: 'none',
    
    // Layout
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    
    // Typography
    fontFamily: typography.fontPrimary,
    fontWeight: typography.weightMedium,
    lineHeight: typography.lineHeightNormal,
    
    // Visual
    borderRadius: layout.radiusMd,
    transformOrigin: 'center',
    transform: 'scale(1)',
    transition: motion.transitionBase,
    
    // GPU acceleration
    transformStyle: 'preserve-3d',
    backfaceVisibility: 'hidden',
    willChange: 'transform',
    
    // States
    ':hover': {
      transform: 'scale(1.05)',
    },
    
    ':active': {
      animation: `${scaleDown} 150ms ease-out`,
    },
    
    ':focus-visible': {
      outline: `2px solid ${colors.primary}`,
      outlineOffset: '2px',
    },
    
    ':disabled': {
      opacity: 0.5,
      cursor: 'not-allowed',
      pointerEvents: 'none',
      transform: 'none',
    },
  },
  
  // Variants
  primary: {
    background: gradients.buttonPrimary,
    color: colors.textLight,
    boxShadow: `${shadows.md}, 0 0 20px rgba(37, 99, 235, 0.25)`,
    
    ':hover': {
      background: gradients.buttonPrimaryHover,
      boxShadow: `${shadows.lg}, 0 0 30px rgba(37, 99, 235, 0.35)`,
    },
    
    ':active': {
      background: colors.primaryActive,
    },
  },
  
  secondary: {
    background: gradients.buttonSecondary,
    color: colors.gray900,
    boxShadow: `${shadows.md}, 0 0 20px rgba(156, 163, 175, 0.25)`,
    
    ':hover': {
      background: gradients.buttonSecondaryHover,
      boxShadow: `${shadows.lg}, 0 0 30px rgba(156, 163, 175, 0.35)`,
    },
  },
  
  success: {
    background: gradients.buttonSuccess,
    color: colors.textLight,
    boxShadow: `${shadows.md}, 0 0 20px rgba(5, 150, 105, 0.25)`,
    
    ':hover': {
      background: `linear-gradient(to right, ${colors.successDark}, ${colors.success})`,
      boxShadow: `${shadows.lg}, 0 0 30px rgba(5, 150, 105, 0.35)`,
    },
  },
  
  danger: {
    background: gradients.buttonDanger,
    color: colors.textLight,
    boxShadow: `${shadows.md}, 0 0 20px rgba(220, 38, 38, 0.25)`,
    
    ':hover': {
      background: `linear-gradient(to right, ${colors.dangerDark}, ${colors.danger})`,
      boxShadow: `${shadows.lg}, 0 0 30px rgba(220, 38, 38, 0.35)`,
    },
  },
  
  ghost: {
    backgroundColor: 'transparent',
    color: colors.gray700,
    border: `1px solid ${colors.gray300}`,
    boxShadow: 'none',
    
    ':hover': {
      backgroundColor: colors.gray100,
      boxShadow: `0 0 20px rgba(107, 114, 128, 0.15)`,
      borderColor: colors.gray500,
    },
  },
  
  outline: {
    backgroundColor: 'transparent',
    border: `2px solid ${colors.primary}`,
    color: colors.primary,
    boxShadow: 'none',
    
    ':hover': {
      backgroundColor: 'rgba(37, 99, 235, 0.05)',
      borderColor: colors.primaryHover,
      boxShadow: `0 0 20px rgba(37, 99, 235, 0.25)`,
    },
  },
  
  // Sizes
  small: {
    paddingBlock: spacing.xs,
    paddingInline: spacing.sm,
    fontSize: typography.textSm,
  },
  
  medium: {
    paddingBlock: spacing.sm,
    paddingInline: spacing.md,
    fontSize: typography.textMd,
  },
  
  large: {
    paddingBlock: spacing.md,
    paddingInline: spacing.lg,
    fontSize: typography.textLg,
  },
  
  // States
  fullWidth: {
    width: '100%',
  },
  
  loading: {
    position: 'relative',
    color: 'transparent',
    pointerEvents: 'none',
  },
  
  // Loading spinner
  spinner: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    width: '16px',
    height: '16px',
    border: '2px solid currentColor',
    borderTopColor: 'transparent',
    borderRadius: layout.radiusFull,
    animation: `${spin} 0.6s linear infinite`,
  },
  
  content: {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.sm,
  },
  
  icon: {
    width: '16px',
    height: '16px',
    display: 'inline-block',
    flexShrink: 0,
  },
});

const Button = memo(
  ({
    children,
    variant = 'primary',
    size = 'medium',
    disabled = false,
    loading = false,
    onClick,
    className = '',
    type = 'button',
    loadingText = 'Loading...',
    icon = null,
    fullWidth = false,
    ...props
  }) => {
    const handleClick = (e) => {
      if (disabled || loading) return;
      onClick?.(e);
    };

    // Get the appropriate button color for the spinner
    const spinnerColor = variant === 'ghost' || variant === 'outline' 
      ? colors.primary 
      : colors.textLight;

    return (
      <button
        type={type}
        disabled={disabled || loading}
        onClick={handleClick}
        {...stylex.props(
          styles.base,
          styles[variant],
          size !== 'medium' && styles[size],
          fullWidth && styles.fullWidth,
          loading && styles.loading,
          // Allow className for migration period
          className && { className }
        )}
        {...props}
      >
        {loading ? (
          <>
            <div 
              {...stylex.props(styles.spinner)}
              style={{ borderColor: spinnerColor, borderTopColor: 'transparent' }}
            />
            <span style={{ opacity: 0 }}>{loadingText}</span>
          </>
        ) : (
          <div {...stylex.props(styles.content)}>
            {icon && <span {...stylex.props(styles.icon)}>{icon}</span>}
            <span>{children}</span>
          </div>
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';

export default Button;