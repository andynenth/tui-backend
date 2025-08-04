// frontend/src/components/GameWithDisconnectHandling.stylex.jsx

import React from 'react';
import * as stylex from '@stylexjs/stylex';
import { spacing } from '../design-system/tokens.stylex';
import ConnectionIndicator from './ConnectionIndicator.stylex';
import ReconnectionPrompt from './ReconnectionPrompt.stylex';
import ToastContainer from './ToastContainer.stylex';
import { useConnectionStatus } from '../hooks/useConnectionStatus';
import { useAutoReconnect } from '../hooks/useAutoReconnect';
import { useDisconnectedPlayers } from '../hooks/useDisconnectedPlayers';
import { useToastNotifications } from '../hooks/useToastNotifications';

// GameWithDisconnectHandling styles
const styles = stylex.create({
  container: {
    position: 'relative',
    width: '100%',
    height: '100%',
  },
  
  connectionStatusArea: {
    position: 'absolute',
    top: '1rem',
    right: '1rem',
    zIndex: 100,
  },
});

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
  className = '',
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

  // Apply container styles
  const containerProps = stylex.props(styles.container);
  
  // During migration, allow combining with existing CSS classes
  const combinedContainerProps = className 
    ? { ...containerProps, className: `${containerProps.className || ''} ${className}`.trim() }
    : containerProps;

  return (
    <div {...combinedContainerProps}>
      {/* Connection status indicator with AI playing info */}
      <div {...stylex.props(styles.connectionStatusArea)}>
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