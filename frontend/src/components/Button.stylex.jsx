import React, { memo } from 'react';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, motion, shadows, layout, gradients } from '../design-system/tokens.stylex';
import { animations } from '../design-system/utils.stylex';

// Button styles
const styles = stylex.create({
  base: {
    // Reset
    border: 'none',
    background: 'none',
    font: 'inherit',
    cursor: 'pointer',
    outline: 'none',
    
    // Layout
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    
    // Typography
    fontFamily: typography.fontPrimary,
    fontWeight: typography.weightSemibold,
    lineHeight: typography.lineHeightNormal,
    
    // Visual
    borderRadius: layout.radiusMd,
    transition: `all ${motion.durationBase} ${motion.easeOut}`,
    transformOrigin: 'center',
    
    // Interaction
    userSelect: 'none',
    
    ':hover': {
      transform: 'scale(1.05)',
      boxShadow: shadows.lg,
    },
    
    ':active': {
      transform: 'scale(0.95)',
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
    background: gradients.primary,
    color: colors.white,
    boxShadow: shadows.primaryGlow,
    
    ':hover': {
      background: `linear-gradient(135deg, ${colors.primaryDark} 0%, ${colors.primary} 100%)`,
      boxShadow: `0 8px 16px rgba(13, 110, 253, 0.3)`,
    },
  },
  
  secondary: {
    background: `linear-gradient(135deg, ${colors.gray200} 0%, ${colors.gray300} 100%)`,
    color: colors.gray800,
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.06)',
    
    ':hover': {
      background: `linear-gradient(135deg, ${colors.gray300} 0%, ${colors.gray400} 100%)`,
      boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)',
    },
  },
  
  success: {
    background: gradients.success,
    color: colors.white,
    boxShadow: shadows.successGlow,
    
    ':hover': {
      background: `linear-gradient(135deg, ${colors.successLight} 0%, ${colors.success} 100%)`,
      boxShadow: `0 8px 16px rgba(40, 167, 69, 0.3)`,
    },
  },
  
  danger: {
    background: gradients.danger,
    color: colors.white,
    boxShadow: shadows.dangerGlow,
    
    ':hover': {
      background: `linear-gradient(135deg, ${colors.dangerDark} 0%, ${colors.danger} 100%)`,
      boxShadow: `0 8px 16px rgba(220, 53, 69, 0.3)`,
    },
  },
  
  ghost: {
    backgroundColor: 'transparent',
    color: colors.gray700,
    border: `1px solid ${colors.gray300}`,
    
    ':hover': {
      backgroundColor: colors.gray100,
      boxShadow: '0 2px 4px rgba(0, 0, 0, 0.04)',
    },
  },
  
  outline: {
    backgroundColor: 'transparent',
    border: `2px solid ${colors.primary}`,
    color: colors.primary,
    
    ':hover': {
      backgroundColor: 'rgba(13, 110, 253, 0.05)',
      borderColor: colors.primaryDark,
    },
  },
  
  // Sizes
  sm: {
    paddingTop: spacing.xs,
    paddingBottom: spacing.xs,
    paddingLeft: spacing.md,
    paddingRight: spacing.md,
    fontSize: typography.textSm,
  },
  
  md: {
    paddingTop: spacing.sm,
    paddingBottom: spacing.sm,
    paddingLeft: spacing.lg,
    paddingRight: spacing.lg,
    fontSize: typography.textBase,
  },
  
  lg: {
    paddingTop: spacing.md,
    paddingBottom: spacing.md,
    paddingLeft: spacing.xxl,
    paddingRight: spacing.xxl,
    fontSize: typography.textLg,
  },
  
  // States
  fullWidth: {
    width: '100%',
  },
  
  loading: {
    position: 'relative',
    color: 'transparent',
  },
});

// Loading spinner styles
const spinnerStyles = stylex.create({
  container: {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.sm,
  },
  
  spinner: {
    width: '16px',
    height: '16px',
    border: '2px solid currentColor',
    borderTopColor: 'transparent',
    borderRadius: '50%',
    animation: `${animations.spin} 0.6s linear infinite`,
  },
  
  text: {
    color: 'inherit',
  },
});

// Icon container styles
const iconStyles = stylex.create({
  container: {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.sm,
  },
  
  icon: {
    width: '16px',
    height: '16px',
    flexShrink: 0,
  },
});

const Button = memo(
  ({
    children,
    variant = 'primary',
    size = 'md',
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

    // Apply StyleX styles
    const buttonProps = stylex.props(
      styles.base,
      styles[variant],
      styles[size],
      fullWidth && styles.fullWidth,
      loading && styles.loading,
    );

    // During migration, allow combining with existing CSS classes
    const combinedProps = className 
      ? { ...buttonProps, className: `${buttonProps.className || ''} ${className}`.trim() }
      : buttonProps;

    return (
      <button
        type={type}
        {...combinedProps}
        disabled={disabled || loading}
        onClick={handleClick}
        {...props}
      >
        {loading ? (
          <div {...stylex.props(spinnerStyles.container)}>
            <div {...stylex.props(spinnerStyles.spinner)} />
            <span {...stylex.props(spinnerStyles.text)}>{loadingText}</span>
          </div>
        ) : (
          <div {...stylex.props(iconStyles.container)}>
            {icon && <span {...stylex.props(iconStyles.icon)}>{icon}</span>}
            <span>{children}</span>
          </div>
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';

export default Button;