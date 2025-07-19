// frontend/src/hooks/useToastNotifications.js

import { useState, useEffect, useCallback, useRef } from 'react';
import { gameService } from '../services/GameService';

/**
 * Hook for managing toast notifications
 * Listens to GameService state changes and triggers toasts for disconnect/reconnect events
 */
export function useToastNotifications() {
  const [toasts, setToasts] = useState([]);
  const previousDisconnectedPlayers = useRef([]);
  const previousHost = useRef(null);
  const toastIdCounter = useRef(0);

  // Generate unique toast ID
  const generateToastId = () => {
    toastIdCounter.current += 1;
    return `toast-${Date.now()}-${toastIdCounter.current}`;
  };

  // Add a new toast
  const addToast = useCallback((toast) => {
    const id = generateToastId();
    const newToast = {
      id,
      message: toast.message,
      type: toast.type || 'info', // 'info', 'warning', 'error', 'success'
      duration: toast.duration || 5000,
      timestamp: Date.now(),
    };

    setToasts((prev) => [...prev, newToast]);

    // Auto-remove after duration
    if (newToast.duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, newToast.duration);
    }

    return id;
  }, []);

  // Remove a toast
  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  // Clear all toasts
  const clearToasts = useCallback(() => {
    setToasts([]);
  }, []);

  // Listen to GameService state changes
  useEffect(() => {
    const handleStateChange = (state) => {
      const currentDisconnectedPlayers = state.disconnectedPlayers || [];

      // Check for newly disconnected players
      const newlyDisconnected = currentDisconnectedPlayers.filter(
        (player) => !previousDisconnectedPlayers.current.includes(player)
      );

      // Check for reconnected players
      const reconnected = previousDisconnectedPlayers.current.filter(
        (player) => !currentDisconnectedPlayers.includes(player)
      );

      // Show toast for each newly disconnected player
      newlyDisconnected.forEach((playerName) => {
        addToast({
          message: `${playerName} disconnected - AI is now playing for them`,
          type: 'warning',
          duration: 7000,
        });
      });

      // Show toast for each reconnected player
      reconnected.forEach((playerName) => {
        addToast({
          message: `${playerName} reconnected and resumed control`,
          type: 'success',
          duration: 5000,
        });
      });

      // Check for host changes
      if (
        state.host !== previousHost.current &&
        previousHost.current !== null
      ) {
        addToast({
          message: `${state.host} is now the host`,
          type: 'info',
          duration: 5000,
        });
      }

      // Update the references
      previousDisconnectedPlayers.current = [...currentDisconnectedPlayers];
      previousHost.current = state.host;
    };

    // Subscribe to GameService
    const unsubscribe = gameService.addListener(handleStateChange);

    // Get initial state
    const initialState = gameService.getState();
    if (initialState.disconnectedPlayers) {
      previousDisconnectedPlayers.current = [
        ...initialState.disconnectedPlayers,
      ];
    }
    if (initialState.host) {
      previousHost.current = initialState.host;
    }

    return () => {
      unsubscribe();
    };
  }, [addToast]);

  // Also listen for custom disconnect events if needed
  useEffect(() => {
    const handlePlayerDisconnected = (event) => {
      const { playerName, isBot } = event.detail || {};
      if (playerName && isBot) {
        addToast({
          message: `${playerName} disconnected - AI is now playing for them`,
          type: 'warning',
          duration: 7000,
        });
      }
    };

    const handlePlayerReconnected = (event) => {
      const { playerName } = event.detail || {};
      if (playerName) {
        addToast({
          message: `${playerName} reconnected and resumed control`,
          type: 'success',
          duration: 5000,
        });
      }
    };

    // Listen to custom events if GameService dispatches them
    window.addEventListener('player_disconnected', handlePlayerDisconnected);
    window.addEventListener('player_reconnected', handlePlayerReconnected);

    return () => {
      window.removeEventListener(
        'player_disconnected',
        handlePlayerDisconnected
      );
      window.removeEventListener('player_reconnected', handlePlayerReconnected);
    };
  }, [addToast]);

  return {
    toasts,
    addToast,
    removeToast,
    clearToasts,
  };
}

export default useToastNotifications;
