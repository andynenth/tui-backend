// frontend/src/components/ConnectionStatusBadge.jsx

import React from 'react';
import '../styles/connection-badges.css';

const ConnectionStatusBadge = ({ connectionStatus, isBot }) => {
  if (!connectionStatus || connectionStatus === 'connected') {
    return null;
  }

  const getStatusClass = () => {
    if (isBot) return 'connection-badge--bot-active';
    if (connectionStatus === 'disconnected') return 'connection-badge--disconnected';
    if (connectionStatus === 'reconnecting') return 'connection-badge--reconnecting';
    return '';
  };

  const getStatusContent = () => {
    if (isBot) {
      return (
        <>
          <span className="connection-badge__icon">🤖</span>
          <span className="connection-badge__text">AI Playing</span>
        </>
      );
    }
    if (connectionStatus === 'disconnected') {
      return <span className="connection-badge__dot connection-badge__dot--red" />;
    }
    if (connectionStatus === 'reconnecting') {
      return <span className="connection-badge__dot connection-badge__dot--yellow" />;
    }
    return null;
  };

  return (
    <div className={`connection-badge ${getStatusClass()}`}>
      {getStatusContent()}
    </div>
  );
};

export default ConnectionStatusBadge;