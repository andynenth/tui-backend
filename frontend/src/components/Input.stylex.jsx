import React, { forwardRef } from 'react';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, motion, layout } from '../design-system/tokens.stylex';

// Input styles
const styles = stylex.create({
  container: {
    display: 'block',
  },
  
  fullWidth: {
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
  
  input: {
    // Reset
    appearance: 'none',
    background: 'none',
    
    // Layout
    display: 'block',
    width: '100%',
    
    // Typography
    fontFamily: typography.fontPrimary,
    lineHeight: typography.lineHeightNormal,
    
    // Visual
    backgroundColor: colors.white,
    border: `1px solid ${colors.gray300}`,
    borderRadius: layout.radiusMd,
    transition: `all ${motion.durationFast} ${motion.easeInOut}`,
    
    // States
    ':hover:not(:disabled)': {
      borderColor: colors.gray400,
    },
    
    ':focus': {
      outline: 'none',
      borderColor: colors.primary,
      boxShadow: `0 0 0 3px rgba(13, 110, 253, 0.1)`,
    },
    
    ':disabled': {
      opacity: 0.5,
      cursor: 'not-allowed',
      backgroundColor: colors.gray100,
    },
    
    '::placeholder': {
      color: colors.gray400,
    },
  },
  
  // Input sizes
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
    paddingLeft: spacing.xl,
    paddingRight: spacing.xl,
    fontSize: typography.textLg,
  },
  
  // Error state
  error: {
    borderColor: colors.danger,
    
    ':hover:not(:disabled)': {
      borderColor: colors.dangerDark,
    },
    
    ':focus': {
      borderColor: colors.danger,
      boxShadow: `0 0 0 3px rgba(220, 53, 69, 0.1)`,
    },
  },
  
  message: {
    marginTop: spacing.xs,
    fontSize: typography.textSm,
  },
  
  errorMessage: {
    color: colors.danger,
  },
  
  helperText: {
    color: colors.gray500,
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
      label = '',
      helperText = '',
      size = 'md',
      fullWidth = false,
      className = '',
      ...props
    },
    ref
  ) => {
    // Apply container styles
    const containerProps = stylex.props(
      styles.container,
      fullWidth && styles.fullWidth
    );

    // Apply input styles
    const inputProps = stylex.props(
      styles.input,
      styles[size],
      error && styles.error
    );

    // During migration, allow combining with existing CSS classes
    const combinedInputProps = className 
      ? { ...inputProps, className: `${inputProps.className || ''} ${className}`.trim() }
      : inputProps;

    return (
      <div {...containerProps}>
        {/* Label */}
        {label && (
          <label {...stylex.props(styles.label)}>
            {label}
            {required && <span {...stylex.props(styles.required)}>*</span>}
          </label>
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
          {...combinedInputProps}
          {...props}
        />

        {/* Error message */}
        {error && (
          <p 
            {...stylex.props(styles.message, styles.errorMessage)} 
            role="alert"
          >
            {error}
          </p>
        )}

        {/* Helper text */}
        {helperText && !error && (
          <p {...stylex.props(styles.message, styles.helperText)}>
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export default Input;