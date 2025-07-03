/**
 * 🌐 **useConnectionStatus Hook** - Network Connection State Management (TypeScript)
 * 
 * Phase 2, Task 2.1: Clean React Hooks
 * 
 * Features:
 * ✅ Single responsibility - only connection status
 * ✅ Real-time connection monitoring
 * ✅ TypeScript interfaces for type safety
 * ✅ Network metrics and diagnostics
 * ✅ Connection health indicators
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { gameStore } from '../stores/UnifiedGameStore';
import type { ConnectionStatus } from '../services/types';

/**
 * Connection state information
 */
export interface ConnectionState extends ConnectionStatus {
  roomId: string | null;
}

/**
 * Hook for monitoring connection status
 */
export function useConnectionStatus(roomId?: string): ConnectionState {
  const [connectionState, setConnectionState] = useState<ConnectionState>(() => {
    const state = gameStore.getState();
    return {
      ...state.connectionStatus,
      roomId: state.roomId
    };
  });

  useEffect(() => {
    const unsubscribe = gameStore.subscribe((state) => {
      setConnectionState({
        ...state.connectionStatus,
        roomId: state.roomId
      });
    });

    return unsubscribe;
  }, []);

  return connectionState;
}

export default useConnectionStatus;