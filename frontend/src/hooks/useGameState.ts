/**
 * 🎮 **useGameState Hook** - Optimized Game State Integration (TypeScript)
 *
 * Phase 2, Task 2.1: Clean React Hooks
 *
 * Features:
 * ✅ Single responsibility - only game state
 * ✅ Optimized re-rendering with selective updates
 * ✅ TypeScript interfaces for type safety
 * ✅ Proper cleanup and memory management
 * ✅ Development debugging helpers
 */

import { useState, useEffect, useRef, useMemo } from 'react';
import { gameService } from '../services/GameService';
import type { GameState } from '../services/types';

/**
 * Hook for accessing game state with optimized updates
 */
export function useGameState(): GameState {
  const [state, setState] = useState<GameState>(() => gameService.getState());
  const stateRef = useRef(state);

  useEffect(() => {
    const handleStateChange = (newState: GameState) => {
      // Only update if state actually changed (deep comparison would be expensive)
      // GameService already handles immutable updates, so reference comparison is sufficient
      if (stateRef.current !== newState) {
        // DEBUG: Log state transitions for debugging UI updates
        console.log('🎮 useGameState: State transition detected');
        console.log('🎮 useGameState: Previous phase:', stateRef.current?.phase);
        console.log('🎮 useGameState: New phase:', newState?.phase);
        console.log('🎮 useGameState: Previous myHand length:', stateRef.current?.myHand?.length);
        console.log('🎮 useGameState: New myHand length:', newState?.myHand?.length);
        console.log('🎮 useGameState: New state object:', newState);
        
        stateRef.current = newState;
        setState(newState);
      }
    };

    // Add listener for state changes
    const cleanup = gameService.addListener(handleStateChange);

    // Ensure we have the latest state on mount
    const currentState = gameService.getState();
    if (stateRef.current !== currentState) {
      stateRef.current = currentState;
      setState(currentState);
    }

    return cleanup;
  }, []);

  return state;
}

/**
 * Hook for accessing specific parts of game state with fine-grained updates
 * Useful for components that only need specific state slices
 */
export function useGameStateSlice<T>(
  selector: (state: GameState) => T,
  equalityFn?: (a: T, b: T) => boolean
): T {
  const [selectedState, setSelectedState] = useState<T>(() =>
    selector(gameService.getState())
  );
  const selectedStateRef = useRef(selectedState);
  const selectorRef = useRef(selector);
  selectorRef.current = selector;

  useEffect(() => {
    const handleStateChange = (newState: GameState) => {
      const newSelectedState = selectorRef.current(newState);

      // Use custom equality function or default shallow comparison
      const hasChanged = equalityFn
        ? !equalityFn(selectedStateRef.current, newSelectedState)
        : selectedStateRef.current !== newSelectedState;

      if (hasChanged) {
        selectedStateRef.current = newSelectedState;
        setSelectedState(newSelectedState);
      }
    };

    const cleanup = gameService.addListener(handleStateChange);

    // Ensure we have the latest selected state on mount
    const currentSelectedState = selectorRef.current(gameService.getState());
    if (selectedStateRef.current !== currentSelectedState) {
      selectedStateRef.current = currentSelectedState;
      setSelectedState(currentSelectedState);
    }

    return cleanup;
  }, [equalityFn]);

  return selectedState;
}

/**
 * Hook for accessing connection state specifically
 * Optimized for components that only care about connection status
 */
export function useConnectionState() {
  return useGameStateSlice(
    (state) => ({
      isConnected: state.isConnected,
      roomId: state.roomId,
      playerName: state.playerName,
      error: state.error,
    }),
    // Custom equality for connection state
    (a, b) =>
      a.isConnected === b.isConnected &&
      a.roomId === b.roomId &&
      a.playerName === b.playerName &&
      a.error === b.error
  );
}

/**
 * Hook for accessing phase-specific state
 * Returns null when not in the specified phase
 */
export function usePhaseState<T>(
  phase: GameState['phase'],
  selector: (state: GameState) => T
): T | null {
  return useGameStateSlice(
    (state) => (state.phase === phase ? selector(state) : null),
    (a, b) => {
      if (a === null && b === null) return true;
      if (a === null || b === null) return false;
      return a === b;
    }
  );
}

/**
 * Hook for accessing player-specific state
 * Useful for components that show current player's data
 */
export function usePlayerState() {
  return useGameStateSlice(
    (state) => ({
      playerName: state.playerName,
      isMyTurn: state.isMyTurn,
      allowedActions: state.allowedActions,
      validOptions: state.validOptions,
      myHand: state.myHand,
    }),
    // Custom equality for player state
    (a, b) =>
      a.playerName === b.playerName &&
      a.isMyTurn === b.isMyTurn &&
      JSON.stringify(a.allowedActions) === JSON.stringify(b.allowedActions) &&
      JSON.stringify(a.validOptions) === JSON.stringify(b.validOptions) &&
      JSON.stringify(a.myHand) === JSON.stringify(b.myHand)
  );
}

/**
 * Hook for accessing game meta information
 * Useful for debugging and status displays
 */
export function useGameMeta() {
  return useGameStateSlice(
    (state) => ({
      phase: state.phase,
      currentRound: state.currentRound,
      lastEventSequence: state.lastEventSequence,
      gameOver: state.gameOver,
      winners: state.winners,
    }),
    // Custom equality for meta state
    (a, b) =>
      a.phase === b.phase &&
      a.currentRound === b.currentRound &&
      a.lastEventSequence === b.lastEventSequence &&
      a.gameOver === b.gameOver &&
      JSON.stringify(a.winners) === JSON.stringify(b.winners)
  );
}

/**
 * Development hook for debugging state changes
 * Only active in development mode
 */
export function useGameStateDebug(componentName: string) {
  const state = useGameState();
  const prevStateRef = useRef(state);

  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      const prevState = prevStateRef.current;

      if (prevState !== state) {
        console.group(`🎮 State Change in ${componentName}`);
        console.log('Previous:', prevState);
        console.log('Current:', state);

        // Log specific changes
        const changes: string[] = [];
        if (prevState.phase !== state.phase)
          changes.push(`phase: ${prevState.phase} → ${state.phase}`);
        if (prevState.isMyTurn !== state.isMyTurn)
          changes.push(`isMyTurn: ${prevState.isMyTurn} → ${state.isMyTurn}`);
        if (prevState.isConnected !== state.isConnected)
          changes.push(
            `isConnected: ${prevState.isConnected} → ${state.isConnected}`
          );
        if (prevState.error !== state.error)
          changes.push(`error: ${prevState.error} → ${state.error}`);

        if (changes.length > 0) {
          console.log('Key changes:', changes.join(', '));
        }

        console.groupEnd();
        prevStateRef.current = state;
      }
    }
  }, [state, componentName]);

  return state;
}

/**
 * Hook for creating derived state calculations
 * Memoizes complex calculations based on game state
 */
export function useDerivedGameState<T>(
  deriveFn: (state: GameState) => T,
  dependencies?: any[]
): T {
  const state = useGameState();

  return useMemo(() => {
    return deriveFn(state);
  }, [state, ...(dependencies || [])]);
}

// Export helper functions for common state checks
export const gameStateSelectors = {
  isInPhase: (phase: GameState['phase']) => (state: GameState) =>
    state.phase === phase,
  hasError: (state: GameState) => state.error !== null,
  isConnected: (state: GameState) => state.isConnected,
  isMyTurn: (state: GameState) => state.isMyTurn,
  canPerformAction: (action: string) => (state: GameState) =>
    state.allowedActions.includes(action),
  getPlayerByName: (name: string) => (state: GameState) =>
    state.players.find((p) => p.name === name),
  getCurrentPlayer: (state: GameState) =>
    state.players.find((p) => p.name === state.playerName),
  getPlayersInOrder: (state: GameState) =>
    state.declarationOrder.length > 0
      ? state.declarationOrder
          .map((name) => state.players.find((p) => p.name === name))
          .filter(Boolean)
      : state.players,
};

export default useGameState;
