// frontend/src/components/ReconnectionPrompt.jsx

import React from 'react';
import PropTypes from 'prop-types';
import { formatSessionInfo } from '../utils/sessionStorage';
import '../styles/reconnection-prompt.css';

const ReconnectionPrompt = ({
  _sessionInfo,
  onReconnect,
  onJoinAsNew,
  isReconnecting,
  isDuplicateTab,
  error,
}) => {
  const formattedInfo = formatSessionInfo();

  if (!formattedInfo) return null;

  return (
    <div className="reconnection-prompt-overlay">
      <div className="reconnection-prompt">
        <div className="reconnection-icon">{isDuplicateTab ? '⚠️' : '🎮'}</div>

        {isDuplicateTab ? (
          <>
            <h2 className="reconnection-title">Game Already Open</h2>
            <p className="reconnection-message">
              You already have this game open in another tab.
            </p>
            <div className="reconnection-info">
              <div className="info-item">
                <span className="info-label">Room:</span>
                <span className="info-value">{formattedInfo.roomId}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Player:</span>
                <span className="info-value">{formattedInfo.playerName}</span>
              </div>
            </div>
            <p className="reconnection-warning">
              Close this tab or switch to the existing game tab.
            </p>
            <div className="reconnection-actions">
              <button className="btn-secondary" onClick={onJoinAsNew}>
                Join as New Player
              </button>
            </div>
          </>
        ) : (
          <>
            <h2 className="reconnection-title">Welcome Back!</h2>
            <p className="reconnection-message">
              We found your game session. Would you like to rejoin?
            </p>

            <div className="reconnection-info">
              <div className="info-item">
                <span className="info-label">Room:</span>
                <span className="info-value">{formattedInfo.roomId}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Player:</span>
                <span className="info-value">{formattedInfo.playerName}</span>
              </div>
              {formattedInfo.gamePhase && (
                <div className="info-item">
                  <span className="info-label">Phase:</span>
                  <span className="info-value">{formattedInfo.gamePhase}</span>
                </div>
              )}
              <div className="info-item">
                <span className="info-label">Last seen:</span>
                <span
                  className={`info-value ${formattedInfo.isRecent ? 'recent' : ''}`}
                >
                  {formattedInfo.lastSeenText}
                </span>
              </div>
            </div>

            {error && (
              <div className="reconnection-error">
                <span className="error-icon">❌</span>
                <span className="error-text">{error}</span>
              </div>
            )}

            <div className="reconnection-actions">
              <button
                className="btn-primary"
                onClick={onReconnect}
                disabled={isReconnecting}
              >
                {isReconnecting ? (
                  <>
                    <span className="spinner" />
                    Reconnecting...
                  </>
                ) : (
                  'Rejoin Game'
                )}
              </button>
              <button
                className="btn-secondary"
                onClick={onJoinAsNew}
                disabled={isReconnecting}
              >
                Join as New Player
              </button>
            </div>

            <p className="reconnection-note">
              Your AI has been playing for you while you were away.
            </p>
          </>
        )}
      </div>
    </div>
  );
};

ReconnectionPrompt.propTypes = {
  sessionInfo: PropTypes.object,
  onReconnect: PropTypes.func.isRequired,
  onJoinAsNew: PropTypes.func.isRequired,
  isReconnecting: PropTypes.bool,
  isDuplicateTab: PropTypes.bool,
  error: PropTypes.string,
};

export default ReconnectionPrompt;
