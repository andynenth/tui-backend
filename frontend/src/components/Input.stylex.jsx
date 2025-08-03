// Input component with StyleX
import React, { forwardRef } from 'react';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, motion, layout } from '../design-system/tokens.stylex';

const styles = stylex.create({
  container: {
    display: 'block',
  },
  
  containerFullWidth: {
    width: '100%',
  },
  
  label: {
    display: 'block',
    fontSize: typography.textSm,
    fontWeight: typography.weightMedium,
    color: colors.gray700,
    marginBottom: spacing.xs,
  },
  
  required: {
    color: colors.danger,
    marginLeft: spacing.xs,
  },
  
  inputWrapper: {
    position: 'relative',
  },
  
  input: {
    // Reset
    appearance: 'none',
    background: 'none',
    font: 'inherit',
    
    // Base styles
    display: 'block',
    width: '100%',
    border: `1px solid ${colors.gray300}`,
    borderRadius: layout.radiusMd,
    backgroundColor: colors.textLight,
    color: colors.gray900,
    transition: motion.transitionBase,
    fontFamily: typography.fontPrimary,
    lineHeight: typography.lineHeightNormal,
    
    // States
    ':hover:not(:disabled)': {
      borderColor: colors.gray400,
    },
    
    ':focus': {
      outline: 'none',
      borderColor: colors.primary,
      boxShadow: `0 0 0 3px rgba(37, 99, 235, 0.1)`,
    },
    
    ':disabled': {
      opacity: 0.5,
      cursor: 'not-allowed',
      backgroundColor: colors.gray100,
      borderColor: colors.gray200,
    },
    
    '::placeholder': {
      color: colors.gray400,
    },
  },
  
  // Size variants
  sizeSmall: {
    paddingBlock: '6px',
    paddingInline: spacing.sm,
    fontSize: typography.textSm,
  },
  
  sizeMedium: {
    paddingBlock: spacing.sm,
    paddingInline: spacing.md,
    fontSize: typography.textMd,
  },
  
  sizeLarge: {
    paddingBlock: spacing.md,
    paddingInline: '20px',
    fontSize: typography.textLg,
  },
  
  // Error state
  inputError: {
    borderColor: colors.danger,
    
    ':hover:not(:disabled)': {
      borderColor: colors.dangerDark,
    },
    
    ':focus': {
      borderColor: colors.danger,
      boxShadow: `0 0 0 3px rgba(220, 38, 38, 0.1)`,
    },
  },
  
  // Success state
  inputSuccess: {
    borderColor: colors.success,
    
    ':hover:not(:disabled)': {
      borderColor: colors.successDark,
    },
    
    ':focus': {
      borderColor: colors.success,
      boxShadow: `0 0 0 3px rgba(5, 150, 105, 0.1)`,
    },
  },
  
  errorMessage: {
    marginTop: spacing.xs,
    fontSize: typography.textSm,
    color: colors.danger,
    display: 'flex',
    alignItems: 'center',
    gap: spacing.xs,
  },
  
  helperText: {
    marginTop: spacing.xs,
    fontSize: typography.textSm,
    color: colors.gray500,
  },
  
  // Icon support
  withIconLeft: {
    paddingLeft: '40px',
  },
  
  withIconRight: {
    paddingRight: '40px',
  },
  
  iconLeft: {
    position: 'absolute',
    left: spacing.sm,
    top: '50%',
    transform: 'translateY(-50%)',
    color: colors.gray400,
    pointerEvents: 'none',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: '20px',
    height: '20px',
  },
  
  iconRight: {
    position: 'absolute',
    right: spacing.sm,
    top: '50%',
    transform: 'translateY(-50%)',
    color: colors.gray400,
    pointerEvents: 'none',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: '20px',
    height: '20px',
  },
});

const Input = forwardRef(
  (
    {
      type = 'text',
      placeholder = '',
      value,
      onChange,
      onBlur,
      onFocus,
      disabled = false,
      required = false,
      error = null,
      success = false,
      label = '',
      helperText = '',
      size = 'medium',
      fullWidth = false,
      className = '',
      iconLeft = null,
      iconRight = null,
      ...props
    },
    ref
  ) => {
    // Map size prop to style
    const sizeStyle = {
      sm: styles.sizeSmall,
      small: styles.sizeSmall,
      md: styles.sizeMedium,
      medium: styles.sizeMedium,
      lg: styles.sizeLarge,
      large: styles.sizeLarge,
    }[size] || styles.sizeMedium;

    return (
      <div {...stylex.props(
        styles.container,
        fullWidth && styles.containerFullWidth
      )}>
        {/* Label */}
        {label && (
          <label {...stylex.props(styles.label)}>
            {label}
            {required && <span {...stylex.props(styles.required)}>*</span>}
          </label>
        )}

        {/* Input wrapper for icons */}
        <div {...stylex.props(styles.inputWrapper)}>
          {/* Left icon */}
          {iconLeft && (
            <div {...stylex.props(styles.iconLeft)}>
              {iconLeft}
            </div>
          )}

          {/* Input */}
          <input
            ref={ref}
            type={type}
            placeholder={placeholder}
            value={value}
            onChange={onChange}
            onBlur={onBlur}
            onFocus={onFocus}
            disabled={disabled}
            required={required}
            {...stylex.props(
              styles.input,
              sizeStyle,
              error && styles.inputError,
              success && styles.inputSuccess,
              iconLeft && styles.withIconLeft,
              iconRight && styles.withIconRight,
              // Allow className for migration period
              className && { className }
            )}
            {...props}
          />

          {/* Right icon */}
          {iconRight && (
            <div {...stylex.props(styles.iconRight)}>
              {iconRight}
            </div>
          )}
        </div>

        {/* Error message */}
        {error && (
          <p {...stylex.props(styles.errorMessage)} role="alert">
            {error}
          </p>
        )}

        {/* Helper text */}
        {helperText && !error && (
          <p {...stylex.props(styles.helperText)}>{helperText}</p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export default Input;