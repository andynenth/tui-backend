// frontend/src/components/EnhancedToastContainer.stylex.jsx

import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, layout, shadows, motion } from '../design-system/tokens.stylex';

// Animations
const slideIn = stylex.keyframes({
  '0%': {
    opacity: 0,
    transform: 'translateX(100%)',
  },
  '100%': {
    opacity: 1,
    transform: 'translateX(0)',
  },
});

const slideOut = stylex.keyframes({
  '0%': {
    opacity: 1,
    transform: 'translateX(0)',
  },
  '100%': {
    opacity: 0,
    transform: 'translateX(100%)',
  },
});

// Toast styles
const toastStyles = stylex.create({
  toast: {
    display: 'flex',
    alignItems: 'flex-start',
    padding: spacing.md,
    marginBottom: spacing.sm,
    borderWidth: '1px',
    borderStyle: 'solid',
    borderRadius: layout.radiusMd,
    boxShadow: shadows.lg,
    transition: `all ${motion.durationBase} ${motion.easeInOut}`,
  },
  
  toastEntering: {
    animation: `${slideIn} 0.3s ${motion.easeOut} forwards`,
  },
  
  toastExiting: {
    animation: `${slideOut} 0.3s ${motion.easeIn} forwards`,
  },
  
  successToast: {
    backgroundColor: '#f0fdf4',
    borderColor: '#86efac',
    color: '#166534',
  },
  
  errorToast: {
    backgroundColor: '#fef2f2',
    borderColor: '#fca5a5',
    color: '#991b1b',
  },
  
  warningToast: {
    backgroundColor: '#fffbeb',
    borderColor: '#fde047',
    color: '#854d0e',
  },
  
  infoToast: {
    backgroundColor: '#eff6ff',
    borderColor: '#93c5fd',
    color: '#1e40af',
  },
  
  iconContainer: {
    flexShrink: 0,
  },
  
  icon: {
    width: '20px',
    height: '20px',
  },
  
  successIcon: {
    color: '#4ade80',
  },
  
  errorIcon: {
    color: '#f87171',
  },
  
  warningIcon: {
    color: '#facc15',
  },
  
  infoIcon: {
    color: '#60a5fa',
  },
  
  content: {
    marginLeft: spacing.md,
    flex: 1,
  },
  
  title: {
    fontSize: typography.textSm,
    fontWeight: typography.weightSemibold,
    marginBottom: spacing.xs,
  },
  
  message: {
    fontSize: typography.textSm,
  },
  
  closeButton: {
    marginLeft: spacing.md,
    flexShrink: 0,
    display: 'inline-flex',
    color: colors.gray400,
    background: 'transparent',
    border: 'none',
    cursor: 'pointer',
    padding: 0,
    transition: `color ${motion.durationFast} ${motion.easeInOut}`,
    ':hover': {
      color: colors.gray500,
    },
    ':focus': {
      outline: 'none',
    },
  },
  
  closeIcon: {
    width: '16px',
    height: '16px',
  },
});

// Container styles
const containerStyles = stylex.create({
  container: {
    position: 'fixed',
    top: spacing.md,
    right: spacing.md,
    zIndex: 50,
    pointerEvents: 'none',
  },
  
  wrapper: {
    pointerEvents: 'auto',
  },
});

/**
 * Enhanced toast notification with smooth animations
 */
const EnhancedToast = ({ toast, onRemove, index }) => {
  const [isExiting, setIsExiting] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      handleRemove();
    }, toast.duration || 5000);

    return () => clearTimeout(timer);
  }, [toast]);

  const handleRemove = () => {
    setIsExiting(true);
    setTimeout(() => {
      onRemove(toast.id);
    }, 300);
  };

  const getTypeStyles = () => {
    switch (toast.type) {
      case 'success':
        return toastStyles.successToast;
      case 'error':
        return toastStyles.errorToast;
      case 'warning':
        return toastStyles.warningToast;
      case 'info':
      default:
        return toastStyles.infoToast;
    }
  };

  const getIconStyle = () => {
    switch (toast.type) {
      case 'success':
        return toastStyles.successIcon;
      case 'error':
        return toastStyles.errorIcon;
      case 'warning':
        return toastStyles.warningIcon;
      default:
        return toastStyles.infoIcon;
    }
  };

  const getIcon = () => {
    switch (toast.type) {
      case 'success':
        return (
          <svg
            {...stylex.props(toastStyles.icon, getIconStyle())}
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
              clipRule="evenodd"
            />
          </svg>
        );
      case 'error':
        return (
          <svg
            {...stylex.props(toastStyles.icon, getIconStyle())}
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clipRule="evenodd"
            />
          </svg>
        );
      case 'warning':
        return (
          <svg
            {...stylex.props(toastStyles.icon, getIconStyle())}
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>
        );
      default:
        return (
          <svg
            {...stylex.props(toastStyles.icon, getIconStyle())}
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
              clipRule="evenodd"
            />
          </svg>
        );
    }
  };

  return (
    <div
      {...stylex.props(
        toastStyles.toast,
        getTypeStyles(),
        isExiting ? toastStyles.toastExiting : toastStyles.toastEntering
      )}
      style={{ transform: `translateY(${index * 100}%)` }}
    >
      <div {...stylex.props(toastStyles.iconContainer)}>{getIcon()}</div>
      <div {...stylex.props(toastStyles.content)}>
        {toast.title && (
          <h3 {...stylex.props(toastStyles.title)}>{toast.title}</h3>
        )}
        <p {...stylex.props(toastStyles.message)}>{toast.message}</p>
      </div>
      <button
        onClick={handleRemove}
        {...stylex.props(toastStyles.closeButton)}
      >
        <svg {...stylex.props(toastStyles.closeIcon)} fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
            clipRule="evenodd"
          />
        </svg>
      </button>
    </div>
  );
};

/**
 * EnhancedToastContainer Component
 *
 * Container for toast notifications with stacking behavior
 */
const EnhancedToastContainer = ({ maxToasts = 4, className = '' }) => {
  const [toasts, setToasts] = useState([]);

  useEffect(() => {
    // Listen for toast events
    const handleToastEvent = (event) => {
      const { type, title, message, duration } = event.detail;
      addToast({ type, title, message, duration });
    };

    window.addEventListener('show-toast', handleToastEvent);

    return () => {
      window.removeEventListener('show-toast', handleToastEvent);
    };
  }, []);

  const addToast = (toast) => {
    const id = Date.now() + Math.random();
    const newToast = { ...toast, id };

    setToasts((prev) => {
      const updated = [...prev, newToast];
      // Keep only the most recent toasts
      if (updated.length > maxToasts) {
        return updated.slice(-maxToasts);
      }
      return updated;
    });
  };

  const removeToast = (id) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  };

  // Apply container styles
  const containerProps = stylex.props(containerStyles.container);
  
  // During migration, allow combining with existing CSS classes
  const combinedContainerProps = className 
    ? { ...containerProps, className: `${containerProps.className || ''} ${className}`.trim() }
    : containerProps;

  return (
    <div {...combinedContainerProps}>
      <div {...stylex.props(containerStyles.wrapper)}>
        {toasts.map((toast, index) => (
          <EnhancedToast
            key={toast.id}
            toast={toast}
            onRemove={removeToast}
            index={index}
          />
        ))}
      </div>
    </div>
  );
};

EnhancedToast.propTypes = {
  toast: PropTypes.shape({
    id: PropTypes.number.isRequired,
    type: PropTypes.oneOf(['success', 'error', 'warning', 'info']),
    title: PropTypes.string,
    message: PropTypes.string.isRequired,
    duration: PropTypes.number,
  }).isRequired,
  onRemove: PropTypes.func.isRequired,
  index: PropTypes.number.isRequired,
};

EnhancedToastContainer.propTypes = {
  maxToasts: PropTypes.number,
  className: PropTypes.string,
};

// Helper function to show toast
export const showToast = (type, message, title = null, duration = 5000) => {
  window.dispatchEvent(
    new CustomEvent('show-toast', {
      detail: { type, title, message, duration },
    })
  );
};

export default EnhancedToastContainer;