/**
 * React hook for UnifiedGameStore
 * 
 * Provides easy access to game state with automatic subscriptions
 * and cleanup on unmount.
 */

import { useEffect, useState, useCallback } from 'react';
import { gameStore } from '../stores/UnifiedGameStore';

/**
 * Hook to access and subscribe to game store state
 */
export function useGameStore() {
  const [state, setState] = useState(() => gameStore.getState());

  useEffect(() => {
    // Subscribe to store updates
    const unsubscribe = gameStore.subscribe((newState) => {
      setState(newState);
    });

    // Cleanup on unmount
    return unsubscribe;
  }, []);

  return {
    gameState: state.gameState,
    connectionStatus: state.connectionStatus,
    roomId: state.roomId,
    playerName: state.playerName
  };
}

/**
 * Hook to access specific parts of game state with selector
 */
export function useGameStoreSelector<T>(
  selector: (state: ReturnType<typeof gameStore.getState>) => T
): T {
  const [selected, setSelected] = useState<T>(() => 
    selector(gameStore.getState())
  );

  useEffect(() => {
    const unsubscribe = gameStore.subscribe((newState) => {
      const newSelected = selector(newState);
      setSelected(newSelected);
    });

    return unsubscribe;
  }, [selector]);

  return selected;
}

/**
 * Hook to get store update function
 */
export function useGameStoreUpdate() {
  return useCallback((updates: Parameters<typeof gameStore.updateState>[0]) => {
    gameStore.updateState(updates);
  }, []);
}