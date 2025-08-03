// ToastNotification component with StyleX
import React, { useEffect } from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, motion, shadows, layout } from '../design-system/tokens.stylex';

// Animation keyframes
const slideIn = stylex.keyframes({
  '0%': {
    transform: 'translateX(100%)',
    opacity: 0,
  },
  '100%': {
    transform: 'translateX(0)',
    opacity: 1,
  },
});

const slideOut = stylex.keyframes({
  '0%': {
    transform: 'translateX(0)',
    opacity: 1,
  },
  '100%': {
    transform: 'translateX(100%)',
    opacity: 0,
  },
});

const progress = stylex.keyframes({
  '0%': {
    width: '100%',
  },
  '100%': {
    width: '0%',
  },
});

const styles = stylex.create({
  notification: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: spacing.sm,
    padding: spacing.md,
    borderRadius: layout.radiusLg,
    boxShadow: shadows.lg,
    backgroundColor: colors.textLight,
    border: '1px solid',
    position: 'relative',
    minWidth: '300px',
    maxWidth: '500px',
    animation: `${slideIn} ${motion.durationNormal} ${motion.easeOut}`,
    overflow: 'hidden',
    marginBottom: spacing.sm,
  },
  
  // Type variants
  info: {
    borderColor: colors.primary,
    backgroundColor: 'rgba(37, 99, 235, 0.05)',
  },
  
  success: {
    borderColor: colors.success,
    backgroundColor: 'rgba(5, 150, 105, 0.05)',
  },
  
  warning: {
    borderColor: colors.warning,
    backgroundColor: 'rgba(217, 119, 6, 0.05)',
  },
  
  error: {
    borderColor: colors.danger,
    backgroundColor: 'rgba(220, 38, 38, 0.05)',
  },
  
  disconnect: {
    borderColor: colors.danger,
    backgroundColor: 'rgba(220, 38, 38, 0.1)',
    borderWidth: '2px',
  },
  
  reconnect: {
    borderColor: colors.success,
    backgroundColor: 'rgba(5, 150, 105, 0.1)',
    borderWidth: '2px',
  },
  
  aiActivated: {
    borderColor: colors.secondary,
    backgroundColor: 'rgba(124, 58, 237, 0.05)',
    backgroundImage: `linear-gradient(135deg, rgba(124, 58, 237, 0.1) 0%, transparent 100%)`,
  },
  
  icon: {
    fontSize: '20px',
    flexShrink: 0,
    width: '24px',
    height: '24px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  
  iconInfo: {
    color: colors.primary,
  },
  
  iconSuccess: {
    color: colors.success,
  },
  
  iconWarning: {
    color: colors.warning,
  },
  
  iconError: {
    color: colors.danger,
  },
  
  iconDisconnect: {
    color: colors.danger,
  },
  
  iconReconnect: {
    color: colors.success,
  },
  
  iconAi: {
    color: colors.secondary,
  },
  
  content: {
    flex: 1,
    minWidth: 0,
  },
  
  title: {
    fontSize: typography.textMd,
    fontWeight: typography.weightSemibold,
    color: colors.gray900,
    marginBottom: spacing.xs,
    lineHeight: typography.lineHeightTight,
  },
  
  message: {
    fontSize: typography.textSm,
    color: colors.gray700,
    lineHeight: typography.lineHeightNormal,
    wordBreak: 'break-word',
  },
  
  closeButton: {
    background: 'transparent',
    border: 'none',
    padding: spacing.xs,
    marginLeft: spacing.sm,
    marginTop: '-4px',
    marginRight: '-8px',
    cursor: 'pointer',
    fontSize: '24px',
    lineHeight: '1',
    color: colors.gray500,
    opacity: 0.7,
    transition: motion.transitionFast,
    flexShrink: 0,
    
    ':hover': {
      opacity: 1,
      color: colors.gray700,
    },
    
    ':focus-visible': {
      outline: `2px solid ${colors.primary}`,
      outlineOffset: '2px',
      borderRadius: layout.radiusSm,
    },
  },
  
  progressBar: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    height: '3px',
    backgroundColor: 'currentColor',
    opacity: 0.3,
    animation: `${progress} linear`,
  },
  
  progressInfo: {
    backgroundColor: colors.primary,
  },
  
  progressSuccess: {
    backgroundColor: colors.success,
  },
  
  progressWarning: {
    backgroundColor: colors.warning,
  },
  
  progressError: {
    backgroundColor: colors.danger,
  },
  
  progressDisconnect: {
    backgroundColor: colors.danger,
  },
  
  progressReconnect: {
    backgroundColor: colors.success,
  },
  
  progressAi: {
    backgroundColor: colors.secondary,
  },
  
  // Closing animation
  closing: {
    animation: `${slideOut} ${motion.durationFast} ${motion.easeIn} forwards`,
  },
});

const ToastNotification = ({
  id,
  type = 'info',
  title,
  message,
  duration = 5000,
  onClose,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  _position = 'top-right',
}) => {
  const [isClosing, setIsClosing] = React.useState(false);

  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        handleClose();
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [id, duration]);

  const handleClose = () => {
    setIsClosing(true);
    setTimeout(() => {
      onClose(id);
    }, 200); // Match the closing animation duration
  };

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

  const getTypeStyles = () => {
    const typeMap = {
      'disconnect': styles.disconnect,
      'reconnect': styles.reconnect,
      'ai-activated': styles.aiActivated,
      'error': styles.error,
      'warning': styles.warning,
      'success': styles.success,
      'info': styles.info,
    };
    return typeMap[type] || styles.info;
  };

  const getIconColorStyle = () => {
    const iconMap = {
      'disconnect': styles.iconDisconnect,
      'reconnect': styles.iconReconnect,
      'ai-activated': styles.iconAi,
      'error': styles.iconError,
      'warning': styles.iconWarning,
      'success': styles.iconSuccess,
      'info': styles.iconInfo,
    };
    return iconMap[type] || styles.iconInfo;
  };

  const getProgressColorStyle = () => {
    const progressMap = {
      'disconnect': styles.progressDisconnect,
      'reconnect': styles.progressReconnect,
      'ai-activated': styles.progressAi,
      'error': styles.progressError,
      'warning': styles.progressWarning,
      'success': styles.progressSuccess,
      'info': styles.progressInfo,
    };
    return progressMap[type] || styles.progressInfo;
  };

  return (
    <div {...stylex.props(
      styles.notification,
      getTypeStyles(),
      isClosing && styles.closing
    )}>
      <div {...stylex.props(styles.icon, getIconColorStyle())}>
        {getIcon()}
      </div>
      <div {...stylex.props(styles.content)}>
        {title && <div {...stylex.props(styles.title)}>{title}</div>}
        <div {...stylex.props(styles.message)}>{message}</div>
      </div>
      <button
        {...stylex.props(styles.closeButton)}
        onClick={handleClose}
        aria-label="Close notification"
      >
        ×
      </button>
      {duration > 0 && (
        <div
          {...stylex.props(styles.progressBar, getProgressColorStyle())}
          style={{ animationDuration: `${duration}ms` }}
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