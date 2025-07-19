// frontend/src/components/ConnectionIndicator.jsx

import React from 'react';

const ConnectionIndicator = ({
  isConnected = false,
  isConnecting = false,
  isReconnecting = false,
  error = null,
  roomId = null,
  showDetails = false,
  className = '',
  disconnectedPlayers = [],
  showAIStatus = true,
}) => {
  const getStatusInfo = () => {
    if (error) {
      return {
        status: 'error',
        text: 'Connection Error',
        color: 'bg-red-500',
        icon: '❌',
      };
    }

    if (isReconnecting) {
      return {
        status: 'reconnecting',
        text: 'Reconnecting...',
        color: 'bg-yellow-500 animate-pulse',
        icon: '🔄',
      };
    }

    if (isConnecting) {
      return {
        status: 'connecting',
        text: 'Connecting...',
        color: 'bg-yellow-500 animate-pulse',
        icon: '⚡',
      };
    }

    if (isConnected) {
      return {
        status: 'connected',
        text: 'Connected',
        color: 'bg-green-500',
        icon: '✅',
      };
    }

    return {
      status: 'disconnected',
      text: 'Disconnected',
      color: 'bg-gray-500',
      icon: '⚫',
    };
  };

  const statusInfo = getStatusInfo();

  const baseClasses = `
    inline-flex items-center space-x-2 px-3 py-1 rounded-full text-sm font-medium text-white
    ${statusInfo.color}
  `;

  return (
    <div className="connection-indicator-container">
      <div className={`${baseClasses} ${className}`}>
        <span className="text-xs">{statusInfo.icon}</span>
        <span>{statusInfo.text}</span>

        {showDetails && roomId && (
          <span className="text-xs opacity-75">({roomId})</span>
        )}

        {error && showDetails && (
          <span className="text-xs opacity-75" title={error.message || error}>
            ⚠️
          </span>
        )}
      </div>

      {showAIStatus && disconnectedPlayers.length > 0 && (
        <div className="ai-status-message mt-2 px-3 py-2 bg-gray-100 rounded-lg text-sm">
          <div className="flex items-center space-x-2">
            <span className="text-lg">🤖</span>
            <div>
              <p className="font-semibold text-gray-800">
                AI Playing for {disconnectedPlayers.length} player{disconnectedPlayers.length > 1 ? 's' : ''}
              </p>
              <p className="text-xs text-gray-600">
                {disconnectedPlayers.join(', ')} can reconnect anytime
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ConnectionIndicator;
