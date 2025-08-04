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
    gap: spacing.md,
    padding: spacing.lg,
    borderRadius: layout.radiusMd,
    boxShadow: shadows.lg,
    backgroundColor: colors.white,
    border: '1px solid',
    borderColor: colors.gray200,
    position: 'relative',
    overflow: 'hidden',
    minWidth: '300px',
    maxWidth: '400px',
    animation: `${animations.slideIn} ${motion.durationBase} ${motion.easeOut}`,
  },
  
  // Toast types
  info: {
    borderColor: colors.primary,
    backgroundColor: 'rgba(13, 110, 253, 0.05)',
  },
  
  success: {
    borderColor: colors.success,
    backgroundColor: 'rgba(40, 167, 69, 0.05)',
  },
  
  warning: {
    borderColor: colors.warning,
    backgroundColor: 'rgba(255, 193, 7, 0.05)',
  },
  
  error: {
    borderColor: colors.danger,
    backgroundColor: 'rgba(220, 53, 69, 0.05)',
  },
  
  disconnect: {
    borderColor: colors.danger,
    backgroundColor: 'rgba(220, 53, 69, 0.08)',
  },
  
  reconnect: {
    borderColor: colors.success,
    backgroundColor: 'rgba(40, 167, 69, 0.08)',
  },
  
  aiActivated: {
    borderColor: colors.primary,
    backgroundColor: 'rgba(13, 110, 253, 0.08)',
  },
  
  // Toast elements
  icon: {
    fontSize: typography.text2xl,
    flexShrink: 0,
    lineHeight: 1,
  },
  
  content: {
    flex: 1,
    minWidth: 0,
  },
  
  title: {
    fontSize: typography.textBase,
    fontWeight: typography.weightSemibold,
    color: colors.gray800,
    marginBottom: spacing.xs,
  },
  
  message: {
    fontSize: typography.textSm,
    color: colors.gray600,
    lineHeight: typography.lineHeightRelaxed,
  },
  
  closeButton: {
    position: 'absolute',
    top: spacing.sm,
    right: spacing.sm,
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    fontSize: typography.text2xl,
    color: colors.gray400,
    padding: spacing.xs,
    lineHeight: 1,
    transition: `color ${motion.durationFast} ${motion.easeInOut}`,
    
    ':hover': {
      color: colors.gray600,
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
  info: { color: colors.primary },
  success: { color: colors.success },
  warning: { color: colors.warning },
  error: { color: colors.danger },
  disconnect: { color: colors.danger },
  reconnect: { color: colors.success },
  aiActivated: { color: colors.primary },
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
            color: typeStyleKey === 'info' ? colors.primary :
                   typeStyleKey === 'success' ? colors.success :
                   typeStyleKey === 'warning' ? colors.warning :
                   typeStyleKey === 'error' ? colors.danger :
                   typeStyleKey === 'disconnect' ? colors.danger :
                   typeStyleKey === 'reconnect' ? colors.success :
                   typeStyleKey === 'aiActivated' ? colors.primary :
                   colors.gray500
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