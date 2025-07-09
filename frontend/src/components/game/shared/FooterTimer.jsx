import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';

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
 * @param {string} className - Additional CSS classes for styling
 */
const FooterTimer = ({
  duration = 5,
  onComplete,
  prefix = '',
  suffix = 'seconds',
  variant = 'inline',
  className = ''
}) => {
  const [countdown, setCountdown] = useState(duration);

  // Auto-advance timer
  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown(prev => {
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

  // Build class names
  const containerClasses = [
    'footer-timer',
    `footer-timer--${variant}`,
    className
  ].filter(Boolean).join(' ');

  return (
    <div className={containerClasses}>
      <span className="footer-timer__text">
        {prefix && <span className="footer-timer__prefix">{prefix} </span>}
        <span className="footer-timer__count">{countdown}</span>
        {suffix && <span className="footer-timer__suffix"> {suffix}</span>}
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
  className: PropTypes.string
};

export default FooterTimer;