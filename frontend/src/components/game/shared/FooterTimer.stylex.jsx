// FooterTimer component with StyleX
import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, shadows, layout, motion, typography } from '../../../design-system/tokens.stylex';

// Animation keyframes
const pulse = stylex.keyframes({
  '0%, 100%': {
    transform: 'scale(1)',
    opacity: 1,
  },
  '50%': {
    transform: 'scale(1.05)',
    opacity: 0.9,
  },
});

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

const urgentPulse = stylex.keyframes({
  '0%, 100%': {
    backgroundColor: colors.danger,
    transform: 'scale(1)',
  },
  '50%': {
    backgroundColor: colors.dangerDark,
    transform: 'scale(1.02)',
  },
});

const styles = stylex.create({
  container: {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: layout.radiusMd,
    transition: motion.transitionBase,
    animation: `${fadeIn} ${motion.durationNormal} ${motion.easeOut}`,
  },
  
  // Variant styles
  variantInline: {
    padding: `${spacing.sm} ${spacing.md}`,
    backgroundColor: colors.surface,
    border: `1px solid ${colors.border}`,
    boxShadow: shadows.sm,
  },
  
  variantFooter: {
    position: 'fixed',
    bottom: spacing.xl,
    left: '50%',
    transform: 'translateX(-50%)',
    padding: `${spacing.md} ${spacing.lg}`,
    backgroundColor: colors.surface,
    border: `2px solid ${colors.primary}`,
    boxShadow: shadows.lg,
    zIndex: layout.zDropdown,
  },
  
  variantProminent: {
    padding: `${spacing.md} ${spacing.xl}`,
    backgroundColor: colors.primary,
    color: colors.textLight,
    boxShadow: shadows.xl,
    border: 'none',
  },
  
  variantMinimal: {
    padding: spacing.xs,
    backgroundColor: 'transparent',
    border: 'none',
    boxShadow: 'none',
  },
  
  text: {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.xs,
    fontSize: typography.textMd,
    fontWeight: typography.weightMedium,
    color: colors.textDark,
    lineHeight: typography.lineHeightNormal,
  },
  
  prefix: {
    color: colors.gray600,
    fontSize: typography.textSm,
  },
  
  count: {
    fontSize: typography.textXl,
    fontWeight: typography.weightBold,
    color: colors.primary,
    minWidth: '2ch',
    textAlign: 'center',
    animation: `${pulse} 1s ${motion.easeInOut} infinite`,
  },
  
  suffix: {
    color: colors.gray600,
    fontSize: typography.textSm,
  },
  
  // State variations
  urgent: {
    animation: `${urgentPulse} 0.5s ${motion.easeInOut} infinite`,
    border: `2px solid ${colors.danger}`,
  },
  
  urgentCount: {
    color: colors.danger,
    animation: `${pulse} 0.5s ${motion.easeInOut} infinite`,
  },
  
  complete: {
    backgroundColor: colors.success,
    color: colors.textLight,
    animation: 'none',
  },
  
  completeCount: {
    color: colors.textLight,
    animation: 'none',
  },
  
  // Size variations
  sizeSm: {
    padding: `${spacing.xs} ${spacing.sm}`,
    fontSize: typography.textSm,
  },
  
  sizeLg: {
    padding: `${spacing.lg} ${spacing.xl}`,
    fontSize: typography.textLg,
  },
  
  // Progress bar (optional enhancement)
  progressContainer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: '4px',
    backgroundColor: colors.gray200,
    borderRadius: '0 0 8px 8px',
    overflow: 'hidden',
  },
  
  progressBar: {
    height: '100%',
    backgroundColor: colors.primary,
    transition: `width 1s linear`,
    transformOrigin: 'left',
  },
  
  progressBarUrgent: {
    backgroundColor: colors.danger,
  },
});

const FooterTimer = ({
  duration = 5,
  onComplete,
  prefix = '',
  suffix = 'seconds',
  variant = 'inline',
  className = '',
  showProgress = false,
  urgentThreshold = 3,
  size = 'medium',
  autoStart = true,
}) => {
  const [countdown, setCountdown] = useState(duration);
  const [isRunning, setIsRunning] = useState(autoStart);
  const [hasCompleted, setHasCompleted] = useState(false);
  
  // Auto-advance timer
  useEffect(() => {
    if (!isRunning) return;
    
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          setHasCompleted(true);
          setIsRunning(false);
          if (onComplete) {
            onComplete();
          }
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    
    return () => clearInterval(timer);
  }, [onComplete, isRunning]);
  
  // Reset when duration changes
  useEffect(() => {
    setCountdown(duration);
    setHasCompleted(false);
    if (autoStart) {
      setIsRunning(true);
    }
  }, [duration, autoStart]);
  
  const isUrgent = countdown <= urgentThreshold && countdown > 0;
  const progress = ((duration - countdown) / duration) * 100;
  
  // Get variant style
  const getVariantStyle = () => {
    const variantMap = {
      'inline': styles.variantInline,
      'footer': styles.variantFooter,
      'prominent': styles.variantProminent,
      'minimal': styles.variantMinimal,
    };
    return variantMap[variant] || styles.variantInline;
  };
  
  // Get size style
  const getSizeStyle = () => {
    const sizeMap = {
      'small': styles.sizeSm,
      'medium': null,
      'large': styles.sizeLg,
    };
    return sizeMap[size];
  };
  
  return (
    <div {...stylex.props(
      styles.container,
      getVariantStyle(),
      getSizeStyle(),
      isUrgent && styles.urgent,
      hasCompleted && styles.complete,
      className && { className }
    )}>
      <span {...stylex.props(styles.text)}>
        {prefix && (
          <span {...stylex.props(styles.prefix)}>
            {prefix}
          </span>
        )}
        <span {...stylex.props(
          styles.count,
          isUrgent && styles.urgentCount,
          hasCompleted && styles.completeCount
        )}>
          {countdown}
        </span>
        {suffix && (
          <span {...stylex.props(styles.suffix)}>
            {countdown === 1 ? suffix.replace(/s$/, '') : suffix}
          </span>
        )}
      </span>
      
      {showProgress && variant === 'footer' && (
        <div {...stylex.props(styles.progressContainer)}>
          <div
            {...stylex.props(
              styles.progressBar,
              isUrgent && styles.progressBarUrgent
            )}
            style={{ width: `${progress}%` }}
          />
        </div>
      )}
    </div>
  );
};

FooterTimer.propTypes = {
  duration: PropTypes.number,
  onComplete: PropTypes.func,
  prefix: PropTypes.string,
  suffix: PropTypes.string,
  variant: PropTypes.oneOf(['inline', 'footer', 'prominent', 'minimal']),
  className: PropTypes.string,
  showProgress: PropTypes.bool,
  urgentThreshold: PropTypes.number,
  size: PropTypes.oneOf(['small', 'medium', 'large']),
  autoStart: PropTypes.bool,
};

export default FooterTimer;