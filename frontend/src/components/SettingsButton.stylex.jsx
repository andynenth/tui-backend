// frontend/src/components/SettingsButton.stylex.jsx

import React from 'react';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, layout, shadows, motion } from '../design-system/tokens.stylex';
import settingIcon from '../assets/setting.svg';

// SettingsButton styles
const styles = stylex.create({
  button: {
    backgroundColor: colors.white,
    border: `1px solid ${colors.gray300}`,
    borderRadius: layout.radiusMd,
    padding: spacing.sm,
    cursor: 'pointer',
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: `all ${motion.durationFast} ${motion.easeInOut}`,
    ':hover': {
      backgroundColor: colors.gray50,
      borderColor: colors.gray400,
      boxShadow: shadows.md,
      transform: 'scale(1.05)',
    },
    ':active': {
      transform: 'scale(0.95)',
    },
    ':focus': {
      outline: `2px solid ${colors.primary}`,
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