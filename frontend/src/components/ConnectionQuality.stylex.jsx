// frontend/src/components/ConnectionQuality.stylex.jsx

import React from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, motion } from '../design-system/tokens.stylex';
import { useConnectionStatus } from '../hooks/useConnectionStatus';

// Animations
const pulse = stylex.keyframes({
  '0%, 100%': {
    opacity: 1,
  },
  '50%': {
    opacity: 0.5,
  },
});

// ConnectionQuality styles
const styles = stylex.create({
  container: {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.sm,
  },
  
  signalIndicator: {
    display: 'flex',
    alignItems: 'flex-end',
    gap: '2px',
  },
  
  small: {
    width: '16px',
    height: '16px',
  },
  
  medium: {
    width: '24px',
    height: '24px',
  },
  
  large: {
    width: '32px',
    height: '32px',
  },
  
  signalBar: {
    width: '4px',
    transition: `all ${motion.durationBase} ${motion.easeInOut}`,
  },
  
  barInactive: {
    backgroundColor: colors.gray300,
  },
  
  barExcellent: {
    backgroundColor: colors.success,
  },
  
  barGood: {
    backgroundColor: '#86efac', // green-400
  },
  
  barFair: {
    backgroundColor: colors.warning,
  },
  
  barPoor: {
    backgroundColor: colors.danger,
  },
  
  latencyText: {
    fontSize: typography.textXs,
    fontWeight: typography.weightMedium,
  },
  
  latencyExcellent: {
    color: colors.successDark,
  },
  
  latencyGood: {
    color: colors.success,
  },
  
  latencyFair: {
    color: colors.warning,
  },
  
  latencyPoor: {
    color: colors.danger,
  },
  
  latencyOffline: {
    color: colors.gray500,
  },
  
  reconnectingIcon: {
    animation: `${pulse} 2s ${motion.easeInOut} infinite`,
  },
  
  reconnectingSvg: {
    width: '16px',
    height: '16px',
    color: colors.warning,
  },
});

/**
 * ConnectionQuality Component
 *
 * Displays visual indicators for network connection quality
 * Shows signal strength, latency, and connection health
 */
const ConnectionQuality = ({
  roomId,
  size = 'medium',
  showLatency = true,
  className = '',
}) => {
  const { latency, connectionQuality, status } = useConnectionStatus(roomId);

  // Get size style
  const sizeStyle = 
    size === 'small' ? styles.small :
    size === 'large' ? styles.large :
    styles.medium;

  const getQualityStyle = () => {
    if (status !== 'connected') return styles.barInactive;

    switch (connectionQuality) {
      case 'excellent':
        return styles.barExcellent;
      case 'good':
        return styles.barGood;
      case 'fair':
        return styles.barFair;
      case 'poor':
        return styles.barPoor;
      default:
        return styles.barInactive;
    }
  };

  const getSignalBars = () => {
    const bars = [];
    const totalBars = 4;
    let activeBars = 0;

    switch (connectionQuality) {
      case 'excellent':
        activeBars = 4;
        break;
      case 'good':
        activeBars = 3;
        break;
      case 'fair':
        activeBars = 2;
        break;
      case 'poor':
        activeBars = 1;
        break;
      default:
        activeBars = 0;
    }

    const qualityStyle = getQualityStyle();

    for (let i = 0; i < totalBars; i++) {
      const isActive = i < activeBars && status === 'connected';
      const barHeight = `${(i + 1) * 25}%`;

      bars.push(
        <div
          key={i}
          {...stylex.props(
            styles.signalBar,
            isActive ? qualityStyle : styles.barInactive
          )}
          style={{ height: barHeight }}
        />
      );
    }

    return bars;
  };

  const getLatencyText = () => {
    if (status !== 'connected' || !latency) return 'Offline';
    return `${latency}ms`;
  };

  const getLatencyStyle = () => {
    if (status !== 'connected' || !latency) return styles.latencyOffline;

    if (latency < 50) return styles.latencyExcellent;
    if (latency < 100) return styles.latencyGood;
    if (latency < 200) return styles.latencyFair;
    return styles.latencyPoor;
  };

  // Apply container styles
  const containerProps = stylex.props(styles.container);
  
  // During migration, allow combining with existing CSS classes
  const combinedContainerProps = className 
    ? { ...containerProps, className: `${containerProps.className || ''} ${className}`.trim() }
    : containerProps;

  return (
    <div {...combinedContainerProps}>
      {/* Signal Strength Indicator */}
      <div
        {...stylex.props(styles.signalIndicator, sizeStyle)}
        title={`Connection: ${connectionQuality || 'checking'}`}
      >
        {getSignalBars()}
      </div>

      {/* Latency Display */}
      {showLatency && (
        <span {...stylex.props(styles.latencyText, getLatencyStyle())}>
          {getLatencyText()}
        </span>
      )}

      {/* Connection Status Icon */}
      {status === 'reconnecting' && (
        <div {...stylex.props(styles.reconnectingIcon)}>
          <svg
            {...stylex.props(styles.reconnectingSvg)}
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z"
              clipRule="evenodd"
            />
          </svg>
        </div>
      )}
    </div>
  );
};

ConnectionQuality.propTypes = {
  roomId: PropTypes.string.isRequired,
  size: PropTypes.oneOf(['small', 'medium', 'large']),
  showLatency: PropTypes.bool,
  className: PropTypes.string,
};

export default ConnectionQuality;