// frontend/src/components/AppWithReconnection.jsx

import React from 'react';
import useAutoReconnect from '../hooks/useAutoReconnect';
import ReconnectionPrompt from './ReconnectionPrompt';
import ToastContainer from './ToastContainer';

/**
 * Wrapper component that adds reconnection functionality to the app
 */
const AppWithReconnection = ({ children }) => {
  const {
    checking,
    hasSession,
    sessionInfo,
    duplicateTab,
    reconnecting,
    error,
    reconnect,
    joinAsNew,
  } = useAutoReconnect();

  // Don't show anything while checking
  if (checking) {
    return (
      <div className="reconnection-checking">
        <div className="spinner" />
        <p>Checking for active sessions...</p>
      </div>
    );
  }

  // Show reconnection prompt if session found
  if (hasSession && sessionInfo) {
    return (
      <>
        <ReconnectionPrompt
          sessionInfo={sessionInfo}
          onReconnect={reconnect}
          onJoinAsNew={joinAsNew}
          isReconnecting={reconnecting}
          isDuplicateTab={duplicateTab}
          error={error}
        />
        {children}
      </>
    );
  }

  // Normal app flow
  return (
    <>
      {children}
      <ToastContainer position="top-right" />
    </>
  );
};

export default AppWithReconnection;