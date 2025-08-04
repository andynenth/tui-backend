// frontend/src/components/ReconnectionProgress.stylex.jsx

import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, layout, shadows, motion } from '../design-system/tokens.stylex';

// Animations
const fadeIn = stylex.keyframes({
  '0%': {
    opacity: 0,
    transform: 'translateY(10px)',
  },
  '100%': {
    opacity: 1,
    transform: 'translateY(0)',
  },
});

const pulse = stylex.keyframes({
  '0%, 100%': {
    opacity: 1,
  },
  '50%': {
    opacity: 0.5,
  },
});

// ReconnectionProgress styles
const styles = stylex.create({
  container: {
    position: 'fixed',
    bottom: '1rem',
    right: '1rem',
    backgroundColor: '#ffffff',
    borderRadius: '0.375rem',
    boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    padding: '1rem',
    minWidth: '300px',
    transition: `all '300ms' 'cubic-bezier(0.4, 0, 0.2, 1)'`,
    zIndex: 50,
  },
  
  containerScale: {
    transform: 'scale(1)',
  },
  
  containerScaleSuccess: {
    transform: 'scale(1.05)',
  },
  
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: '1rem',
  },
  
  title: {
    fontSize: '0.875rem',
    fontWeight: '600',
    color: '#343a40',
  },
  
  cancelButton: {
    color: '#adb5bd',
    backgroundColor: 'transparent',
    border: 'none',
    cursor: 'pointer',
    padding: 0,
    transition: `color '150ms' 'cubic-bezier(0.4, 0, 0.2, 1)'`,
    ':hover': {
      color: '#495057',
    },
  },
  
  cancelIcon: {
    width: '16px',
    height: '16px',
  },
  
  progressContainer: {
    position: 'relative',
    marginBottom: '0.5rem',
  },
  
  progressBar: {
    height: '8px',
    backgroundColor: '#e9ecef',
    borderRadius: '9999px',
    overflow: 'hidden',
  },
  
  progressFill: {
    height: '100%',
    transition: `width '500ms' 'cubic-bezier(0, 0, 0.2, 1)'`,
  },
  
  progressFillConnecting: {
    backgroundColor: '#0d6efd',
  },
  
  progressFillSuccess: {
    backgroundColor: '#198754',
  },
  
  attemptIndicator: {
    position: 'absolute',
    top: 0,
    left: 0,
    height: '100%',
    pointerEvents: 'none',
  },
  
  attemptLine: {
    height: '100%',
    borderRight: '2px dashed',
    borderRightColor: '#ced4da',
    opacity: 0.5,
  },
  
  statusRow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    fontSize: '0.75rem',
  },
  
  statusText: {
    color: '#6c757d',
  },
  
  successText: {
    color: '#146c43',
    fontWeight: '500',
  },
  
  successAnimation: {
    display: 'flex',
    alignItems: 'center',
    color: '#146c43',
    animation: `${fadeIn} 0.3s 'cubic-bezier(0, 0, 0.2, 1)'`,
  },
  
  successIcon: {
    width: '20px',
    height: '20px',
    marginRight: '0.25rem',
  },
  
  successLabel: {
    fontWeight: '500',
  },
  
  additionalInfo: {
    marginTop: '1rem',
    fontSize: '0.75rem',
    color: '#adb5bd',
  },
  
  pulsingText: {
    animation: `${pulse} 2s 'cubic-bezier(0.4, 0, 0.2, 1)' infinite`,
  },
});

/**
 * ReconnectionProgress Component
 *
 * Shows a progress bar and status during reconnection attempts
 * Includes smooth animations and success/failure states
 */
const ReconnectionProgress = ({
  isReconnecting,
  attemptNumber = 1,
  maxAttempts = 5,
  onCancel,
  className = '',
}) => {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('idle'); // idle, connecting, success, failed
  const [showSuccess, setShowSuccess] = useState(false);

  useEffect(() => {
    if (isReconnecting) {
      setStatus('connecting');
      setProgress(0);
      setShowSuccess(false);

      // Simulate progress
      const interval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 90) {
            clearInterval(interval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      return () => clearInterval(interval);
    } else if (status === 'connecting') {
      // Connection completed
      setProgress(100);
      setStatus('success');
      setShowSuccess(true);

      // Hide after animation
      const timer = setTimeout(() => {
        setStatus('idle');
        setShowSuccess(false);
      }, 2000);

      return () => clearTimeout(timer);
    }
  }, [isReconnecting, status]);

  if (status === 'idle' && !showSuccess) {
    return null;
  }

  const progressPercentage = Math.min(progress, 100);
  const attemptPercentage = (attemptNumber / maxAttempts) * 100;

  // Apply container styles
  const containerProps = stylex.props(
    styles.container,
    showSuccess ? styles.containerScaleSuccess : styles.containerScale
  );
  
  // During migration, allow combining with existing CSS classes
  const combinedContainerProps = className 
    ? { ...containerProps, className: `${containerProps.className || ''} ${className}`.trim() }
    : containerProps;

  return (
    <div {...combinedContainerProps}>
      {/* Header */}
      <div {...stylex.props(styles.header)}>
        <h3 {...stylex.props(styles.title)}>
          {status === 'success' ? 'Reconnected!' : 'Reconnecting...'}
        </h3>
        {status === 'connecting' && onCancel && (
          <button
            onClick={onCancel}
            {...stylex.props(styles.cancelButton)}
            aria-label="Cancel reconnection"
          >
            <svg
              {...stylex.props(styles.cancelIcon)}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        )}
      </div>

      {/* Progress Bar */}
      <div {...stylex.props(styles.progressContainer)}>
        <div {...stylex.props(styles.progressBar)}>
          <div
            {...stylex.props(
              styles.progressFill,
              status === 'success' ? styles.progressFillSuccess : styles.progressFillConnecting
            )}
            style={{ width: `${progressPercentage}%` }}
          />
        </div>

        {/* Attempt indicator */}
        {status === 'connecting' && maxAttempts > 1 && (
          <div {...stylex.props(styles.attemptIndicator)}>
            <div
              {...stylex.props(styles.attemptLine)}
              style={{ width: `${attemptPercentage}%` }}
            />
          </div>
        )}
      </div>

      {/* Status Text */}
      <div {...stylex.props(styles.statusRow)}>
        <span {...stylex.props(styles.statusText)}>
          {status === 'success' ? (
            <span {...stylex.props(styles.successText)}>
              Connection restored
            </span>
          ) : (
            <>
              Attempt {attemptNumber} of {maxAttempts}
            </>
          )}
        </span>

        {/* Success Animation */}
        {showSuccess && (
          <div {...stylex.props(styles.successAnimation)}>
            <svg
              {...stylex.props(styles.successIcon)}
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clipRule="evenodd"
              />
            </svg>
            <span {...stylex.props(styles.successLabel)}>Success!</span>
          </div>
        )}
      </div>

      {/* Additional Info */}
      {status === 'connecting' && (
        <div {...stylex.props(styles.additionalInfo)}>
          <div {...stylex.props(styles.pulsingText)}>Establishing secure connection...</div>
        </div>
      )}
    </div>
  );
};

ReconnectionProgress.propTypes = {
  isReconnecting: PropTypes.bool.isRequired,
  attemptNumber: PropTypes.number,
  maxAttempts: PropTypes.number,
  onCancel: PropTypes.func,
  className: PropTypes.string,
};

export default ReconnectionProgress;