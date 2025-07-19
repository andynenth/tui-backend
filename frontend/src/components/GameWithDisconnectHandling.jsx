// frontend/src/components/GameWithDisconnectHandling.jsx

import React from 'react';
import ConnectionIndicator from './ConnectionIndicator';
import ReconnectionPrompt from './ReconnectionPrompt';
import ToastContainer from './ToastContainer';
import { useConnectionStatus } from '../hooks/useConnectionStatus';
import { useAutoReconnect } from '../hooks/useAutoReconnect';
import { useDisconnectedPlayers } from '../hooks/useDisconnectedPlayers';
import { useToastNotifications } from '../hooks/useToastNotifications';

/**
 * Example integration component showing how to use disconnect handling
 * with the existing game infrastructure
 */
export function GameWithDisconnectHandling({
  roomId,
  playerName,
  gameState,
  players = [],
  children,
}) {
  // Connection status from existing infrastructure
  const connectionState = useConnectionStatus(roomId);

  // Auto-reconnection with browser close recovery
  const {
    showReconnectPrompt,
    attemptReconnect,
    dismissReconnectPrompt,
    isAttemptingReconnect,
  } = useAutoReconnect(roomId, playerName, gameState);

  // Track disconnected players
  const disconnectedPlayers = useDisconnectedPlayers(players);

  // Toast notifications for disconnect events
  const { toasts, removeToast } = useToastNotifications();

  return (
    <div className="game-container">
      {/* Connection status indicator with AI playing info */}
      <div className="connection-status-area">
        <ConnectionIndicator
          isConnected={connectionState.isConnected}
          isConnecting={connectionState.isConnecting}
          isReconnecting={connectionState.isReconnecting}
          error={connectionState.error}
          roomId={roomId}
          showDetails={true}
          disconnectedPlayers={disconnectedPlayers}
        />
      </div>

      {/* Reconnection prompt for browser close recovery */}
      {showReconnectPrompt && (
        <ReconnectionPrompt
          roomId={roomId}
          onReconnect={attemptReconnect}
          onDismiss={dismissReconnectPrompt}
          isReconnecting={isAttemptingReconnect}
        />
      )}

      {/* Toast notifications for disconnect/reconnect events */}
      <ToastContainer toasts={toasts} onRemove={removeToast} />

      {/* Game content */}
      {children}
    </div>
  );
}

export default GameWithDisconnectHandling;
