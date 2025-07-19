// frontend/src/hooks/useAutoReconnect.js

import { useEffect, useState, useCallback, useRef } from 'react';
import {
  useConnectionStatus,
  useConnectionEvents,
} from './useConnectionStatus';
import { networkService } from '../services/NetworkService';
import { sessionManager } from '../utils/sessionStorage';
import { tabManager } from '../utils/tabCommunication';
import { GAME_STATES } from '../constants/gameStates';

/**
 * Hook for automatic reconnection handling with browser close recovery
 * Integrates with existing connection infrastructure
 */
export function useAutoReconnect(roomId, playerName, gameState) {
  const [isAttemptingReconnect, setIsAttemptingReconnect] = useState(false);
  const [reconnectSession, setReconnectSession] = useState(null);
  const [showReconnectPrompt, setShowReconnectPrompt] = useState(false);
  const connectionState = useConnectionStatus(roomId);
  const hasCheckedSession = useRef(false);

  // Check for stored session on mount
  useEffect(() => {
    if (!hasCheckedSession.current) {
      hasCheckedSession.current = true;

      const session = sessionManager.getSession();
      if (session && !connectionState.isConnected) {
        // Check if game is still active
        if (gameState !== GAME_STATES.NO_GAME) {
          setReconnectSession(session);
          setShowReconnectPrompt(true);
        } else {
          // Clear expired session
          sessionManager.clearSession();
        }
      }
    }
  }, [connectionState.isConnected, gameState]);

  // Save session when connected
  useEffect(() => {
    if (connectionState.isConnected && roomId && playerName) {
      sessionManager.saveSession({
        roomId,
        playerName,
        gameState,
      });
    }
  }, [connectionState.isConnected, roomId, playerName, gameState]);

  // Handle multi-tab detection
  useEffect(() => {
    if (connectionState.isConnected && roomId) {
      const cleanup = tabManager.registerTab(roomId, playerName);

      // Listen for duplicate tab events
      const handleDuplicateTab = () => {
        console.warn('Game already open in another tab');
        // Could show a warning to the user
      };

      tabManager.onDuplicateTab(handleDuplicateTab);

      return () => {
        cleanup();
        tabManager.offDuplicateTab(handleDuplicateTab);
      };
    }
  }, [connectionState.isConnected, roomId, playerName]);

  // Handle automatic reconnection
  const attemptReconnect = useCallback(
    async (session) => {
      if (isAttemptingReconnect || connectionState.isConnected) return;

      setIsAttemptingReconnect(true);
      setShowReconnectPrompt(false);

      try {
        // Use existing network service to reconnect
        await networkService.connect(session.roomId, {
          playerName: session.playerName,
          isReconnection: true,
        });

        // Clear session after successful reconnect
        sessionManager.clearSession();
        setReconnectSession(null);
      } catch (error) {
        console.error('Reconnection failed:', error);
        setShowReconnectPrompt(true);
      } finally {
        setIsAttemptingReconnect(false);
      }
    },
    [isAttemptingReconnect, connectionState.isConnected]
  );

  // Connection event handlers
  useConnectionEvents(
    // onConnected
    (connectedRoomId) => {
      if (connectedRoomId === roomId) {
        setIsAttemptingReconnect(false);
        setShowReconnectPrompt(false);
      }
    },
    // onDisconnected
    (disconnectedRoomId) => {
      if (disconnectedRoomId === roomId && playerName) {
        // Save session for recovery
        sessionManager.saveSession({
          roomId,
          playerName,
          gameState,
        });
      }
    },
    // onReconnecting
    () => {
      setIsAttemptingReconnect(true);
    },
    // onError
    () => {
      setIsAttemptingReconnect(false);
    }
  );

  return {
    isAttemptingReconnect,
    reconnectSession,
    showReconnectPrompt,
    attemptReconnect: () =>
      reconnectSession && attemptReconnect(reconnectSession),
    dismissReconnectPrompt: () => {
      setShowReconnectPrompt(false);
      sessionManager.clearSession();
      setReconnectSession(null);
    },
    connectionState,
  };
}

export default useAutoReconnect;
