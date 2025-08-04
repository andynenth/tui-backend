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
    fontSize: '0.875rem',
    fontWeight: '500',
    color: '#495057',
    marginBottom: '0.25rem',
  },
  
  required: {
    color: '#dc3545',
    marginLeft: '0.25rem',
  },
  
  input: {
    // Reset
    appearance: 'none',
    backgroundColor: 'none',
    
    // Layout
    display: 'block',
    width: '100%',
    
    // Typography
    fontFamily: typography.fontPrimary,
    lineHeight: typography.lineHeightNormal,
    
    // Visual
    backgroundColor: '#ffffff',
    borderWidth: '1px',
    borderStyle: 'solid',
    borderColor: '#dee2e6',
    borderRadius: '0.375rem',
    transition: `all '150ms' 'cubic-bezier(0.4, 0, 0.2, 1)'`,
    
    // States
    ':hover:not(:disabled)': {
      borderColor: '#ced4da',
    },
    
    ':focus': {
      outline: 'none',
      borderColor: '#0d6efd',
      boxShadow: `0 0 0 3px rgba(13, 110, 253, 0.1)`,
    },
    
    ':disabled': {
      opacity: 0.5,
      cursor: 'not-allowed',
      backgroundColor: '#f1f3f5',
    },
    
    '::placeholder': {
      color: '#ced4da',
    },
  },
  
  // Input sizes
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
    paddingLeft: '2rem',
    paddingRight: '2rem',
    fontSize: '1.125rem',
  },
  
  // Error state
  error: {
    borderColor: '#dc3545',
    
    ':hover:not(:disabled)': {
      borderColor: '#a71e2a',
    },
    
    ':focus': {
      borderColor: '#dc3545',
      boxShadow: `0 0 0 3px rgba(220, 53, 69, 0.1)`,
    },
  },
  
  message: {
    marginTop: '0.25rem',
    fontSize: '0.875rem',
  },
  
  errorMessage: {
    color: '#dc3545',
  },
  
  helperText: {
    color: '#adb5bd',
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