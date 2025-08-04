import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, motion, layout, shadows } from '../../../design-system/tokens.stylex';

// Timer animation
const countdownPulse = stylex.keyframes({
  '0%': {
    transform: 'scale(1)',
  },
  '50%': {
    transform: 'scale(1.1)',
  },
  '100%': {
    transform: 'scale(1)',
  },
});

// FooterTimer styles
const styles = stylex.create({
  container: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: `all '300ms' 'cubic-bezier(0.4, 0, 0.2, 1)'`,
  },
  
  // Variant styles
  inline: {
    padding: '0.5rem',
    borderRadius: '0.375rem',
    backgroundColor: 'rgba(37, 99, 235, 0.1)',
  },
  
  footer: {
    position: 'fixed',
    bottom: 0,
    left: 0,
    right: 0,
    padding: '1rem',
    backgroundColor: '#ffffff',
    borderTopWidth: '1px',
    borderTopStyle: 'solid',
    borderTopColor: '#e9ecef',
    boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    zIndex: 50,
  },
  
  text: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.25rem',
    fontSize: '1rem',
    color: '#495057',
  },
  
  prefix: {
    fontWeight: '400',
    color: '#6c757d',
  },
  
  count: {
    fontWeight: '700',
    fontSize: '1.125rem',
    color: '#0d6efd',
    animation: `${countdownPulse} 1s 'cubic-bezier(0.4, 0, 0.2, 1)' infinite`,
    display: 'inline-block',
    minWidth: '2ch',
    textAlign: 'center',
  },
  
  countUrgent: {
    color: '#dc3545',
    animationDuration: '0.5s',
  },
  
  suffix: {
    fontWeight: '400',
    color: '#6c757d',
  },
  
  // Special styles for different states
  warning: {
    backgroundColor: 'rgba(245, 158, 11, 0.1)',
    borderColor: '#ffc107',
  },
  
  danger: {
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
    borderColor: '#dc3545',
  },
});

/**
 * FooterTimer Component
 *
 * A unified countdown timer component used across game phases.
 * Displays a countdown and executes a callback when complete.
 *
 * @param {number} duration - Initial countdown value in seconds (default: 5)
 * @param {function} onComplete - Callback function when countdown reaches 0
 * @param {string} prefix - Text to display before the countdown number
 * @param {string} suffix - Text to display after the countdown number (default: "seconds")
 * @param {string} variant - Display variant: 'inline' or 'footer' (default: 'inline')
 * @param {string} className - Additional CSS classes for styling (for migration)
 */
const FooterTimer = ({
  duration = 5,
  onComplete,
  prefix = ',
  suffix = 'seconds',
  variant = 'inline',
  className = '',
}) => {
  const [countdown, setCountdown] = useState(duration);

  // Auto-advance timer
  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          if (onComplete) {
            onComplete();
          }
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [onComplete]);

  // Determine urgency level for styling
  const isUrgent = countdown <= 3;
  const isWarning = countdown <= 5 && countdown > 3;
  
  // Get variant style
  const variantStyle = variant === 'footer' ? styles.footer : styles.inline;
  
  // Get state style
  const stateStyle = isUrgent ? styles.danger : isWarning ? styles.warning : null;
  
  // Apply container styles
  const containerProps = stylex.props(
    styles.container,
    variantStyle,
    stateStyle
  );
  
  // During migration, allow combining with existing CSS classes
  const combinedContainerProps = className 
    ? { ...containerProps, className: `${containerProps.className || ''} ${className}`.trim() }
    : containerProps;

  return (
    <div {...combinedContainerProps}>
      <span {...stylex.props(styles.text)}>
        {prefix && <span {...stylex.props(styles.prefix)}>{prefix} </span>}
        <span {...stylex.props(
          styles.count,
          isUrgent && styles.countUrgent
        )}>
          {countdown}
        </span>
        {suffix && <span {...stylex.props(styles.suffix)}> {suffix}</span>}
      </span>
    </div>
  );
};

FooterTimer.propTypes = {
  duration: PropTypes.number,
  onComplete: PropTypes.func,
  prefix: PropTypes.string,
  suffix: PropTypes.string,
  variant: PropTypes.oneOf(['inline', 'footer']),
  className: PropTypes.string,
};

export default FooterTimer;