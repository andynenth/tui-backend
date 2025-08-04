// frontend/src/components/SettingsButton.stylex.jsx

import React from 'react';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, layout, shadows, motion } from '../design-system/tokens.stylex';
import settingIcon from '../assets/setting.svg';

// SettingsButton styles
const styles = stylex.create({
  button: {
    backgroundColor: '#ffffff',
    borderWidth: '1px',
    borderStyle: 'solid',
    borderColor: '#dee2e6',
    borderRadius: '0.375rem',
    padding: '0.5rem',
    cursor: 'pointer',
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: `all '150ms' 'cubic-bezier(0.4, 0, 0.2, 1)'`,
    ':hover': {
      backgroundColor: '#f8f9fa',
      borderColor: '#ced4da',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
      transform: 'scale(1.05)',
    },
    ':active': {
      transform: 'scale(0.95)',
    },
    ':focus': {
      outline: `2px solid '#0d6efd'`,
      outlineOffset: '2px',
    },
  },
  
  icon: {
    width: '20px',
    height: '20px',
    display: 'block',
  },
});

/**
 * SettingsButton Component
 *
 * A button that opens the settings modal
 */
const SettingsButton = ({ onClick, className = '' }) => {
  // Apply button styles
  const buttonProps = stylex.props(styles.button);
  
  // During migration, allow combining with existing CSS classes
  const combinedButtonProps = className 
    ? { ...buttonProps, className: `${buttonProps.className || ''} ${className}`.trim() }
    : buttonProps;

  return (
    <button {...combinedButtonProps} onClick={onClick} aria-label="Settings">
      <img src={settingIcon} alt="Settings" {...stylex.props(styles.icon)} />
    </button>
  );
};

export default SettingsButton;