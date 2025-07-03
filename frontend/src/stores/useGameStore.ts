// frontend/src/stores/useGameStore.ts

import { useEffect, useState, useCallback, useMemo } from 'react';
import { gameStore, StoreState } from './UnifiedGameStore';

/**
 * React hook to access the unified game store
 * Automatically subscribes to state changes and provides the current state
 */
export function useGameStore() {
  const [state, setState] = useState<StoreState>(gameStore.getState());
  
  useEffect(() => {
    // Subscribe to store changes
    const unsubscribe = gameStore.subscribe((newState) => {
      setState(newState);
    });
    
    // Get initial state
    setState(gameStore.getState());
    
    // Cleanup
    return unsubscribe;
  }, []);
  
  // Memoized dispatch function for actions
  const dispatch = useCallback((action: any) => {
    // In the future, this will dispatch actions
    // For now, direct state updates through gameStore.setState
    console.warn('dispatch not yet implemented, use networkService.send directly');
  }, []);
  
  return {
    gameState: state,
    dispatch
  };
}

/**
 * Hook to select specific parts of the game state
 * Prevents unnecessary re-renders when unrelated state changes
 */
export function useGameStoreSelector<T>(
  selector: (state: StoreState) => T
): T {
  const [selectedState, setSelectedState] = useState<T>(() => 
    selector(gameStore.getState())
  );
  
  useEffect(() => {
    let previousSelected = selectedState;
    
    const unsubscribe = gameStore.subscribe((newState) => {
      const newSelected = selector(newState);
      // Only update if the selected value changed
      if (newSelected !== previousSelected) {
        previousSelected = newSelected;
        setSelectedState(newSelected);
      }
    });
    
    // Get initial selected state
    const currentSelected = selector(gameStore.getState());
    if (currentSelected !== previousSelected) {
      setSelectedState(currentSelected);
    }
    
    return unsubscribe;
  }, [selector, selectedState]);
  
  return selectedState;
}

/**
 * Hook to get the update function for the store
 * Useful when you only need to update state without reading it
 */
export function useGameStoreUpdate() {
  return useCallback((updates: Partial<StoreState>) => {
    gameStore.setState(updates);
  }, []);
}