import React, { useEffect } from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, motion, shadows, layout } from '../design-system/tokens.stylex';
import { animations } from '../design-system/utils.stylex';

// Define progress animation
const progressAnimation = stylex.keyframes({
  '0%': {
    width: '100%',
  },
  '100%': {
    width: '0%',
  },
});

// Toast styles
const styles = stylex.create({
  container: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '1rem',
    padding: '1.5rem',
    borderRadius: '0.375rem',
    boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    backgroundColor: '#ffffff',
    border: '1px solid',
    borderColor: '#e9ecef',
    position: 'relative',
    overflow: 'hidden',
    minWidth: '300px',
    maxWidth: '400px',
    animation: `${animations.slideIn} '300ms' 'cubic-bezier(0, 0, 0.2, 1)'`,
  },
  
  // Toast types
  info: {
    borderColor: '#0d6efd',
    backgroundColor: 'rgba(13, 110, 253, 0.05)',
  },
  
  success: {
    borderColor: '#198754',
    backgroundColor: 'rgba(40, 167, 69, 0.05)',
  },
  
  warning: {
    borderColor: '#ffc107',
    backgroundColor: 'rgba(255, 193, 7, 0.05)',
  },
  
  error: {
    borderColor: '#dc3545',
    backgroundColor: 'rgba(220, 53, 69, 0.05)',
  },
  
  disconnect: {
    borderColor: '#dc3545',
    backgroundColor: 'rgba(220, 53, 69, 0.08)',
  },
  
  reconnect: {
    borderColor: '#198754',
    backgroundColor: 'rgba(40, 167, 69, 0.08)',
  },
  
  aiActivated: {
    borderColor: '#0d6efd',
    backgroundColor: 'rgba(13, 110, 253, 0.08)',
  },
  
  // Toast elements
  icon: {
    fontSize: '1.5rem',
    flexShrink: 0,
    lineHeight: 1,
  },
  
  content: {
    flex: 1,
    minWidth: 0,
  },
  
  title: {
    fontSize: '1rem',
    fontWeight: '600',
    color: '#343a40',
    marginBottom: '0.25rem',
  },
  
  message: {
    fontSize: '0.875rem',
    color: '#6c757d',
    lineHeight: typography.lineHeightRelaxed,
  },
  
  closeButton: {
    position: 'absolute',
    top: '0.5rem',
    right: '0.5rem',
    backgroundColor: 'none',
    border: 'none',
    cursor: 'pointer',
    fontSize: '1.5rem',
    color: '#ced4da',
    padding: '0.25rem',
    lineHeight: 1,
    transition: `color '150ms' 'cubic-bezier(0.4, 0, 0.2, 1)'`,
    
    ':hover': {
      color: '#6c757d',
    },
  },
  
  progress: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    height: '3px',
    backgroundColor: 'currentColor',
    opacity: 0.3,
    // Animation will be applied inline with dynamic duration
  },
});

// Type-specific icon colors
const iconStyles = stylex.create({
  info: { color: '#0d6efd' },
  success: { color: '#198754' },
  warning: { color: '#ffc107' },
  error: { color: '#dc3545' },
  disconnect: { color: '#dc3545' },
  reconnect: { color: '#198754' },
  aiActivated: { color: '#0d6efd' },
});

const ToastNotification = ({
  id,
  type = 'info',
  title,
  message,
  duration = 5000,
  onClose,
  position = 'top-right', // Note: position is handled by container, not individual toasts
}) => {
  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        onClose(id);
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [id, duration, onClose]);

  const getIcon = () => {
    switch (type) {
      case 'disconnect':
        return '🔌';
      case 'reconnect':
        return '🔗';
      case 'ai-activated':
        return '🤖';
      case 'error':
        return '❌';
      case 'warning':
        return '⚠️';
      case 'success':
        return '✅';
      default:
        return 'ℹ️';
    }
  };

  // Map type to style key
  const typeStyleKey = type === 'ai-activated' ? 'aiActivated' : type;

  return (
    <div {...stylex.props(styles.container, styles[typeStyleKey])}>
      <div {...stylex.props(styles.icon, iconStyles[typeStyleKey])}>
        {getIcon()}
      </div>
      <div {...stylex.props(styles.content)}>
        {title && <div {...stylex.props(styles.title)}>{title}</div>}
        <div {...stylex.props(styles.message)}>{message}</div>
      </div>
      <button
        {...stylex.props(styles.closeButton)}
        onClick={() => onClose(id)}
        aria-label="Close notification"
      >
        ×
      </button>
      {duration > 0 && (
        <div
          {...stylex.props(styles.progress)}
          style={{ 
            animation: `${progressAnimation} ${duration}ms linear`,
            color: typeStyleKey === 'info' ? '#0d6efd' :
                   typeStyleKey === 'success' ? '#198754' :
                   typeStyleKey === 'warning' ? '#ffc107' :
                   typeStyleKey === 'error' ? '#dc3545' :
                   typeStyleKey === 'disconnect' ? '#dc3545' :
                   typeStyleKey === 'reconnect' ? '#198754' :
                   typeStyleKey === 'aiActivated' ? '#0d6efd' :
                   '#adb5bd'
          }}
        />
      )}
    </div>
  );
};

ToastNotification.propTypes = {
  id: PropTypes.string.isRequired,
  type: PropTypes.oneOf([
    'info',
    'success',
    'warning',
    'error',
    'disconnect',
    'reconnect',
    'ai-activated',
  ]),
  title: PropTypes.string,
  message: PropTypes.string.isRequired,
  duration: PropTypes.number,
  onClose: PropTypes.func.isRequired,
  position: PropTypes.oneOf([
    'top-left',
    'top-right',
    'bottom-left',
    'bottom-right',
  ]),
};

export default ToastNotification;