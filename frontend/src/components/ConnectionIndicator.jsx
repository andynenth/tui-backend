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

  const hasDisconnectedPlayers = disconnectedPlayers.length > 0;

  return (
    <div className="flex flex-col gap-2">
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

      {hasDisconnectedPlayers && (
        <div className="text-xs text-gray-600 bg-yellow-100 px-3 py-1 rounded-full">
          <span className="mr-1">🤖</span>
          AI Playing for: {disconnectedPlayers.join(', ')} - Can reconnect anytime
        </div>
      )}
    </div>
  );
};

export default ConnectionIndicator;
