// frontend/src/components/HostIndicator.stylex.jsx

import React from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, layout } from '../design-system/tokens.stylex';

// HostIndicator styles
const styles = stylex.create({
  indicator: {
    display: 'inline-flex',
    alignItems: 'center',
    backgroundColor: colors.warning,
    color: '#92400e', // yellow-900
    fontWeight: typography.weightMedium,
    borderRadius: layout.radiusSm,
  },
  
  small: {
    fontSize: typography.textXs,
    paddingTop: '2px',
    paddingBottom: '2px',
    paddingLeft: '6px',
    paddingRight: '6px',
  },
  
  medium: {
    fontSize: typography.textSm,
    paddingTop: spacing.xs,
    paddingBottom: spacing.xs,
    paddingLeft: spacing.sm,
    paddingRight: spacing.sm,
  },
  
  large: {
    fontSize: typography.textBase,
    paddingTop: '6px',
    paddingBottom: '6px',
    paddingLeft: spacing.md,
    paddingRight: spacing.md,
  },
  
  crown: {
    marginRight: spacing.xs,
  },
});

/**
 * HostIndicator Component
 *
 * Displays a crown icon or "HOST" badge to indicate who is the current room host.
 * Can be used alongside player names or avatars.
 */
const HostIndicator = ({ isHost, size = 'medium', className = '' }) => {
  if (!isHost) return null;

  // Get size style
  const sizeStyle = 
    size === 'small' ? styles.small :
    size === 'large' ? styles.large :
    styles.medium;

  // Apply indicator styles
  const indicatorProps = stylex.props(styles.indicator, sizeStyle);
  
  // During migration, allow combining with existing CSS classes
  const combinedIndicatorProps = className 
    ? { ...indicatorProps, className: `${indicatorProps.className || ''} ${className}`.trim() }
    : indicatorProps;

  return (
    <span
      {...combinedIndicatorProps}
      title="Room Host"
    >
      <span {...stylex.props(styles.crown)}>👑</span>
      <span>HOST</span>
    </span>
  );
};

HostIndicator.propTypes = {
  isHost: PropTypes.bool.isRequired,
  size: PropTypes.oneOf(['small', 'medium', 'large']),
  className: PropTypes.string,
};

export default HostIndicator;