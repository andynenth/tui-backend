// frontend/src/components/ConnectionQuality.jsx

import React from 'react';
import PropTypes from 'prop-types';
import { useConnectionStatus } from '../hooks/useConnectionStatus';

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

  const getSizeClasses = () => {
    switch (size) {
      case 'small':
        return 'w-4 h-4';
      case 'large':
        return 'w-8 h-8';
      default:
        return 'w-6 h-6';
    }
  };

  const getQualityColor = () => {
    if (status !== 'connected') return 'text-gray-400';

    switch (connectionQuality) {
      case 'excellent':
        return 'text-green-500';
      case 'good':
        return 'text-green-400';
      case 'fair':
        return 'text-yellow-500';
      case 'poor':
        return 'text-red-500';
      default:
        return 'text-gray-400';
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

    for (let i = 0; i < totalBars; i++) {
      const isActive = i < activeBars && status === 'connected';
      const barHeight = `${(i + 1) * 25}%`;

      bars.push(
        <div
          key={i}
          className={`w-1 transition-all duration-300 ${
            isActive ? getQualityColor() : 'bg-gray-300'
          }`}
          style={{ height: barHeight }}
        />
      );
    }

    return bars;
  };

  const getLatencyText = () => {
    if (status !== 'connected' || !latency) return 'Offline';

    if (latency < 50) return `${latency}ms`;
    if (latency < 100) return `${latency}ms`;
    if (latency < 200) return `${latency}ms`;
    return `${latency}ms`;
  };

  const getLatencyColor = () => {
    if (status !== 'connected' || !latency) return 'text-gray-500';

    if (latency < 50) return 'text-green-600';
    if (latency < 100) return 'text-green-500';
    if (latency < 200) return 'text-yellow-500';
    return 'text-red-500';
  };

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {/* Signal Strength Indicator */}
      <div
        className={`flex items-end gap-0.5 ${getSizeClasses()}`}
        title={`Connection: ${connectionQuality || 'checking'}`}
      >
        {getSignalBars()}
      </div>

      {/* Latency Display */}
      {showLatency && (
        <span className={`text-xs font-medium ${getLatencyColor()}`}>
          {getLatencyText()}
        </span>
      )}

      {/* Connection Status Icon */}
      {status === 'reconnecting' && (
        <div className="animate-pulse">
          <svg
            className="w-4 h-4 text-yellow-500"
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
