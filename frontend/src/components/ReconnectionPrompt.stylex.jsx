// frontend/src/components/ReconnectionPrompt.stylex.jsx

import React from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, layout, shadows, motion } from '../design-system/tokens.stylex';
import { formatSessionInfo } from '../utils/sessionStorage';

// Animations
const spin = stylex.keyframes({
  '0%': {
    transform: 'rotate(0deg)',
  },
  '100%': {
    transform: 'rotate(360deg)',
  },
});

// ReconnectionPrompt styles
const styles = stylex.create({
  overlay: {
    position: 'fixed',
    inset: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 100,
    padding: '1rem',
  },
  
  prompt: {
    backgroundColor: '#ffffff',
    borderRadius: '0.5rem',
    padding: '2rem',
    maxWidth: '450px',
    width: '100%',
    boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  },
  
  icon: {
    fontSize: '48px',
    textAlign: 'center',
    marginBottom: '1rem',
  },
  
  title: {
    fontSize: '1.5rem',
    fontWeight: '700',
    color: '#212529',
    marginBottom: '0.5rem',
    textAlign: 'center',
  },
  
  message: {
    fontSize: '1rem',
    color: '#6c757d',
    marginBottom: '1.5rem',
    textAlign: 'center',
  },
  
  info: {
    backgroundColor: '#f8f9fa',
    borderRadius: '0.375rem',
    padding: '1rem',
    marginBottom: '1.5rem',
  },
  
  infoItem: {
    display: 'flex',
    justifyContent: 'space-between',
    paddingTop: '0.25rem',
    paddingBottom: '0.25rem',
  },
  
  infoLabel: {
    fontSize: '0.875rem',
    color: '#adb5bd',
    fontWeight: '500',
  },
  
  infoValue: {
    fontSize: '0.875rem',
    color: '#212529',
    fontWeight: '500',
  },
  
  infoValueRecent: {
    color: '#146c43',
  },
  
  warning: {
    fontSize: '0.875rem',
    color: '#cc9a06',
    textAlign: 'center',
    marginTop: '1rem',
    fontWeight: '500',
  },
  
  error: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    backgroundColor: '#fef2f2',
    borderWidth: '1px',
    borderStyle: 'solid',
    borderColor: '#dc3545',
    borderRadius: '0.375rem',
    padding: '1rem',
    marginBottom: '1.5rem',
  },
  
  errorIcon: {
    fontSize: '1.125rem',
  },
  
  errorText: {
    fontSize: '0.875rem',
    color: '#a71e2a',
  },
  
  actions: {
    display: 'flex',
    gap: '1rem',
    marginTop: '1.5rem',
  },
  
  button: {
    flex: 1,
    padding: `'0.5rem' '1.5rem'`,
    borderRadius: '0.375rem',
    fontSize: '1rem',
    fontWeight: '500',
    border: 'none',
    cursor: 'pointer',
    transition: `all '150ms' 'cubic-bezier(0.4, 0, 0.2, 1)'`,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '0.5rem',
  },
  
  buttonPrimary: {
    backgroundColor: '#0d6efd',
    color: '#ffffff',
    ':hover:not(:disabled)': {
      backgroundColor: '#0056b3',
    },
    ':disabled': {
      opacity: 0.5,
      cursor: 'not-allowed',
    },
  },
  
  buttonSecondary: {
    backgroundColor: '#e9ecef',
    color: '#495057',
    ':hover:not(:disabled)': {
      backgroundColor: '#dee2e6',
    },
    ':disabled': {
      opacity: 0.5,
      cursor: 'not-allowed',
    },
  },
  
  spinner: {
    display: 'inline-block',
    width: '16px',
    height: '16px',
    border: '2px solid rgba(255, 255, 255, 0.3)',
    borderTopColor: '#ffffff',
    borderRadius: '50%',
    animation: `${spin} 0.6s linear infinite`,
  },
  
  note: {
    fontSize: '0.75rem',
    color: '#adb5bd',
    textAlign: 'center',
    marginTop: '1rem',
    fontStyle: 'italic',
  },
});

/**
 * ReconnectionPrompt Component
 *
 * Displays a prompt for reconnecting to a previous game session
 * Handles both reconnection and duplicate tab scenarios
 */
const ReconnectionPrompt = ({
  sessionInfo,
  onReconnect,
  onJoinAsNew,
  isReconnecting,
  isDuplicateTab,
  error,
  className = '',
}) => {
  const formattedInfo = formatSessionInfo();

  if (!formattedInfo) return null;

  // Apply overlay styles
  const overlayProps = stylex.props(styles.overlay);
  
  // During migration, allow combining with existing CSS classes
  const combinedOverlayProps = className 
    ? { ...overlayProps, className: `${overlayProps.className || ''} ${className}`.trim() }
    : overlayProps;

  return (
    <div {...combinedOverlayProps}>
      <div {...stylex.props(styles.prompt)}>
        <div {...stylex.props(styles.icon)}>{isDuplicateTab ? '⚠️' : '🎮'}</div>

        {isDuplicateTab ? (
          <>
            <h2 {...stylex.props(styles.title)}>Game Already Open</h2>
            <p {...stylex.props(styles.message)}>
              You already have this game open in another tab.
            </p>
            <div {...stylex.props(styles.info)}>
              <div {...stylex.props(styles.infoItem)}>
                <span {...stylex.props(styles.infoLabel)}>Room:</span>
                <span {...stylex.props(styles.infoValue)}>{formattedInfo.roomId}</span>
              </div>
              <div {...stylex.props(styles.infoItem)}>
                <span {...stylex.props(styles.infoLabel)}>Player:</span>
                <span {...stylex.props(styles.infoValue)}>{formattedInfo.playerName}</span>
              </div>
            </div>
            <p {...stylex.props(styles.warning)}>
              Close this tab or switch to the existing game tab.
            </p>
            <div {...stylex.props(styles.actions)}>
              <button 
                {...stylex.props(styles.button, styles.buttonSecondary)} 
                onClick={onJoinAsNew}
              >
                Join as New Player
              </button>
            </div>
          </>
        ) : (
          <>
            <h2 {...stylex.props(styles.title)}>Welcome Back!</h2>
            <p {...stylex.props(styles.message)}>
              We found your game session. Would you like to rejoin?
            </p>

            <div {...stylex.props(styles.info)}>
              <div {...stylex.props(styles.infoItem)}>
                <span {...stylex.props(styles.infoLabel)}>Room:</span>
                <span {...stylex.props(styles.infoValue)}>{formattedInfo.roomId}</span>
              </div>
              <div {...stylex.props(styles.infoItem)}>
                <span {...stylex.props(styles.infoLabel)}>Player:</span>
                <span {...stylex.props(styles.infoValue)}>{formattedInfo.playerName}</span>
              </div>
              {formattedInfo.gamePhase && (
                <div {...stylex.props(styles.infoItem)}>
                  <span {...stylex.props(styles.infoLabel)}>Phase:</span>
                  <span {...stylex.props(styles.infoValue)}>{formattedInfo.gamePhase}</span>
                </div>
              )}
              <div {...stylex.props(styles.infoItem)}>
                <span {...stylex.props(styles.infoLabel)}>Last seen:</span>
                <span
                  {...stylex.props(
                    styles.infoValue,
                    formattedInfo.isRecent && styles.infoValueRecent
                  )}
                >
                  {formattedInfo.lastSeenText}
                </span>
              </div>
            </div>

            {error && (
              <div {...stylex.props(styles.error)}>
                <span {...stylex.props(styles.errorIcon)}>❌</span>
                <span {...stylex.props(styles.errorText)}>{error}</span>
              </div>
            )}

            <div {...stylex.props(styles.actions)}>
              <button
                {...stylex.props(styles.button, styles.buttonPrimary)}
                onClick={onReconnect}
                disabled={isReconnecting}
              >
                {isReconnecting ? (
                  <>
                    <span {...stylex.props(styles.spinner)} />
                    Reconnecting...
                  </>
                ) : (
                  'Rejoin Game'
                )}
              </button>
              <button
                {...stylex.props(styles.button, styles.buttonSecondary)}
                onClick={onJoinAsNew}
                disabled={isReconnecting}
              >
                Join as New Player
              </button>
            </div>

            <p {...stylex.props(styles.note)}>
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
  className: PropTypes.string,
};

export default ReconnectionPrompt;