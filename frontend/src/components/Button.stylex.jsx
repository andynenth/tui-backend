import React, { memo } from 'react';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, motion, shadows, layout, gradients } from '../design-system/tokens.stylex';
import { animations } from '../design-system/utils.stylex';

// Button styles
const styles = stylex.create({
  base: {
    // Reset
    border: 'none',
    backgroundColor: 'none',
    font: 'inherit',
    cursor: 'pointer',
    outline: 'none',
    
    // Layout
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '0.5rem',
    
    // Typography
    fontFamily: typography.fontPrimary,
    fontWeight: '600',
    lineHeight: typography.lineHeightNormal,
    
    // Visual
    borderRadius: '0.375rem',
    transition: `all '300ms' 'cubic-bezier(0, 0, 0.2, 1)'`,
    transformOrigin: 'center',
    
    // Interaction
    userSelect: 'none',
    
    ':hover': {
      transform: 'scale(1.05)',
      boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    },
    
    ':active': {
      transform: 'scale(0.95)',
    },
    
    ':focus-visible': {
      outline: `2px solid '#0d6efd'`,
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
    color: '#ffffff',
    boxShadow: shadows.primaryGlow,
    
    ':hover': {
      backgroundImage: `linear-gradient(135deg, '#0056b3' 0%, '#0d6efd' 100%)`,
      boxShadow: `0 8px 16px rgba(13, 110, 253, 0.3)`,
    },
  },
  
  secondary: {
    backgroundImage: `linear-gradient(135deg, '#e9ecef' 0%, '#dee2e6' 100%)`,
    color: '#343a40',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.06)',
    
    ':hover': {
      backgroundImage: `linear-gradient(135deg, '#dee2e6' 0%, '#ced4da' 100%)`,
      boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)',
    },
  },
  
  success: {
    background: gradients.success,
    color: '#ffffff',
    boxShadow: shadows.successGlow,
    
    ':hover': {
      backgroundImage: `linear-gradient(135deg, ${colors.successLight} 0%, '#198754' 100%)`,
      boxShadow: `0 8px 16px rgba(40, 167, 69, 0.3)`,
    },
  },
  
  danger: {
    background: gradients.danger,
    color: '#ffffff',
    boxShadow: shadows.dangerGlow,
    
    ':hover': {
      backgroundImage: `linear-gradient(135deg, '#a71e2a' 0%, '#dc3545' 100%)`,
      boxShadow: `0 8px 16px rgba(220, 53, 69, 0.3)`,
    },
  },
  
  ghost: {
    backgroundColor: 'transparent',
    color: '#495057',
    borderWidth: '1px',
    borderStyle: 'solid',
    borderColor: '#dee2e6',
    
    ':hover': {
      backgroundColor: '#f1f3f5',
      boxShadow: '0 2px 4px rgba(0, 0, 0, 0.04)',
    },
  },
  
  outline: {
    backgroundColor: 'transparent',
    borderWidth: '2px',
    borderStyle: 'solid',
    borderColor: '#0d6efd',
    color: '#0d6efd',
    
    ':hover': {
      backgroundColor: 'rgba(13, 110, 253, 0.05)',
      borderColor: '#0056b3',
    },
  },
  
  // Sizes
  sm: {
    paddingTop: '0.25rem',
    paddingBottom: '0.25rem',
    paddingLeft: '1rem',
    paddingRight: '1rem',
    fontSize: '0.875rem',
  },
  
  md: {
    paddingTop: '0.5rem',
    paddingBottom: '0.5rem',
    paddingLeft: '1.5rem',
    paddingRight: '1.5rem',
    fontSize: '1rem',
  },
  
  lg: {
    paddingTop: '1rem',
    paddingBottom: '1rem',
    paddingLeft: '3rem',
    paddingRight: '3rem',
    fontSize: '1.125rem',
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
    gap: '0.5rem',
  },
  
  spinner: {
    width: '16px',
    height: '16px',
    borderWidth: '2px',
    borderStyle: 'solid',
    borderColor: 'currentColor',
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
    gap: '0.5rem',
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