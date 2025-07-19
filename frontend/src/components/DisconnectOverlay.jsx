// frontend/src/components/DisconnectOverlay.jsx

import React from 'react';
import '../styles/disconnect-overlay.css';

const DisconnectOverlay = ({ 
  isDisconnected, 
  connectionStatus, 
  playerName,
  isBot,
  onReconnect 
}) => {
  if (!isDisconnected && connectionStatus !== 'reconnecting') {
    return null;
  }

  const getMessage = () => {
    if (connectionStatus === 'reconnecting') {
      return (
        <>
          <div className="disconnect-overlay__spinner" />
          <p className="disconnect-overlay__text">Reconnecting...</p>
        </>
      );
    }

    if (isBot) {
      return (
        <>
          <div className="disconnect-overlay__icon">🤖</div>
          <p className="disconnect-overlay__text">AI is playing for {playerName}</p>
          <p className="disconnect-overlay__subtext">They can reconnect anytime</p>
        </>
      );
    }

    return (
      <>
        <div className="disconnect-overlay__icon">⚠️</div>
        <p className="disconnect-overlay__text">Connection Lost</p>
        <p className="disconnect-overlay__subtext">Attempting to reconnect...</p>
        {onReconnect && (
          <button 
            className="disconnect-overlay__button"
            onClick={onReconnect}
          >
            Retry Connection
          </button>
        )}
      </>
    );
  };

  return (
    <div className="disconnect-overlay">
      <div className="disconnect-overlay__content">
        {getMessage()}
      </div>
    </div>
  );
};

export default DisconnectOverlay;