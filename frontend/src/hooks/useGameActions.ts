/**
 * 🎯 **useGameActions Hook** - Memoized Game Action Handlers (TypeScript)
 * 
 * Phase 2, Task 2.1: Clean React Hooks
 * 
 * Features:
 * ✅ Single responsibility - only game actions
 * ✅ Memoized action callbacks for performance
 * ✅ TypeScript interfaces for type safety
 * ✅ Error handling with user feedback
 * ✅ Action validation and state checking
 */

import { useCallback, useMemo } from 'react';
import { gameService } from '../services/GameService';
import { serviceIntegration } from '../services/ServiceIntegration';
import type { GameState, ErrorRecoveryResult } from '../services/types';
import { useGameState } from './useGameState';

/**
 * Game action callbacks with memoization
 */
export interface GameActions {
  // Connection actions
  connectToRoom: (roomId: string, playerName: string) => Promise<void>;
  disconnectFromRoom: () => Promise<void>;
  
  // Preparation phase actions
  acceptRedeal: () => Promise<void>;
  declineRedeal: () => Promise<void>;
  
  // Declaration phase actions
  makeDeclaration: (value: number) => Promise<void>;
  
  // Turn phase actions
  playPieces: (indices: number[]) => Promise<void>;
  
  // Scoring phase actions
  startNextRound: () => Promise<void>;
  
  // Recovery actions
  triggerRecovery: (errorType?: string) => Promise<ErrorRecoveryResult>;
  emergencyReset: () => Promise<void>;
  
  // Utility actions
  refreshState: () => void;
  clearError: () => void;
}

/**
 * Configuration for action behavior
 */
export interface GameActionsConfig {
  enableLogging?: boolean;
  throwOnError?: boolean;
  validateState?: boolean;
}

/**
 * Hook for accessing memoized game actions
 */
export function useGameActions(config: GameActionsConfig = {}): GameActions {
  const gameState = useGameState();
  const {
    enableLogging = process.env.NODE_ENV === 'development',
    throwOnError = false,
    validateState = true
  } = config;

  // Helper function for action logging
  const logAction = useCallback((actionName: string, params?: any) => {
    if (enableLogging) {
      console.log(`🎯 Action: ${actionName}`, params || '');
    }
  }, [enableLogging]);

  // Helper function for error handling
  const handleActionError = useCallback((actionName: string, error: unknown) => {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    console.error(`❌ Action ${actionName} failed:`, error);
    
    if (throwOnError) {
      throw error;
    }
    
    return errorMessage;
  }, [throwOnError]);

  // Helper function for state validation
  const validateActionState = useCallback((
    actionName: string,
    requiredPhase?: GameState['phase'],
    requiredConnected: boolean = true
  ): boolean => {
    if (!validateState) return true;

    if (requiredConnected && !gameState.isConnected) {
      console.warn(`Cannot ${actionName}: Not connected to game`);
      return false;
    }

    if (requiredPhase && gameState.phase !== requiredPhase) {
      console.warn(`Cannot ${actionName}: Wrong phase (current: ${gameState.phase}, required: ${requiredPhase})`);
      return false;
    }

    if (gameState.error) {
      console.warn(`Cannot ${actionName}: Game has error - ${gameState.error}`);
      return false;
    }

    return true;
  }, [gameState, validateState]);

  // Connection Actions
  const connectToRoom = useCallback(async (roomId: string, playerName: string) => {
    try {
      logAction('connectToRoom', { roomId, playerName });
      
      if (!roomId || !playerName) {
        throw new Error('Room ID and player name are required');
      }

      await serviceIntegration.connectToRoom(roomId, playerName);
    } catch (error) {
      handleActionError('connectToRoom', error);
      throw error;
    }
  }, [logAction, handleActionError]);

  const disconnectFromRoom = useCallback(async () => {
    try {
      logAction('disconnectFromRoom');
      await serviceIntegration.disconnectFromRoom();
    } catch (error) {
      handleActionError('disconnectFromRoom', error);
      throw error;
    }
  }, [logAction, handleActionError]);

  // Preparation Phase Actions
  const acceptRedeal = useCallback(async () => {
    try {
      logAction('acceptRedeal');
      
      if (!validateActionState('acceptRedeal', 'preparation')) {
        return;
      }

      if (!gameState.isMyDecision) {
        throw new Error('Not your turn to make redeal decision');
      }

      gameService.acceptRedeal();
    } catch (error) {
      handleActionError('acceptRedeal', error);
      if (throwOnError) throw error;
    }
  }, [logAction, validateActionState, gameState.isMyDecision, handleActionError, throwOnError]);

  const declineRedeal = useCallback(async () => {
    try {
      logAction('declineRedeal');
      
      if (!validateActionState('declineRedeal', 'preparation')) {
        return;
      }

      if (!gameState.isMyDecision) {
        throw new Error('Not your turn to make redeal decision');
      }

      gameService.declineRedeal();
    } catch (error) {
      handleActionError('declineRedeal', error);
      if (throwOnError) throw error;
    }
  }, [logAction, validateActionState, gameState.isMyDecision, handleActionError, throwOnError]);

  // Declaration Phase Actions
  const makeDeclaration = useCallback(async (value: number) => {
    try {
      logAction('makeDeclaration', { value });
      
      if (!validateActionState('makeDeclaration', 'declaration')) {
        return;
      }

      if (!gameState.isMyTurn) {
        throw new Error('Not your turn to declare');
      }

      if (typeof value !== 'number' || value < 0 || value > 8) {
        throw new Error('Declaration value must be between 0 and 8');
      }

      // Validate against last player total=8 rule
      const declarationCount = Object.keys(gameState.declarations).length;
      const totalPlayers = gameState.players.length;
      const isLastPlayer = declarationCount === totalPlayers - 1;
      
      if (isLastPlayer) {
        const currentTotal = Object.values(gameState.declarations).reduce((sum, val) => sum + val, 0);
        if (currentTotal + value === 8) {
          throw new Error('Last player cannot make total equal 8');
        }
      }

      gameService.makeDeclaration(value);
    } catch (error) {
      handleActionError('makeDeclaration', error);
      if (throwOnError) throw error;
    }
  }, [logAction, validateActionState, gameState.isMyTurn, gameState.declarations, gameState.players.length, handleActionError, throwOnError]);

  // Turn Phase Actions
  const playPieces = useCallback(async (indices: number[]) => {
    
    try {
      logAction('playPieces', { indices });
      
      const isValid = validateActionState('playPieces', 'turn');
      
      if (!isValid) {
        return;
      }

      if (!gameState.isMyTurn) {
        throw new Error('Not your turn to play pieces');
      }

      if (!Array.isArray(indices) || indices.length === 0) {
        throw new Error('Must select at least one piece to play');
      }

      if (indices.some(i => i < 0 || i >= gameState.myHand.length)) {
        throw new Error('Invalid piece indices selected');
      }

      // Validate piece count matches required (if set)
      if (gameState.requiredPieceCount !== null && indices.length !== gameState.requiredPieceCount) {
        throw new Error(`Must play exactly ${gameState.requiredPieceCount} pieces`);
      }

      // Remove duplicates
      const uniqueIndices = Array.from(new Set(indices));
      if (uniqueIndices.length !== indices.length) {
        throw new Error('Cannot play the same piece multiple times');
      }

      gameService.playPieces(uniqueIndices);
    } catch (error) {
      handleActionError('playPieces', error);
      if (throwOnError) throw error;
    }
  }, [logAction, validateActionState, gameState.isMyTurn, gameState.myHand.length, gameState.requiredPieceCount, handleActionError, throwOnError, gameState]);

  // Scoring Phase Actions
  const startNextRound = useCallback(async () => {
    try {
      logAction('startNextRound');
      
      if (!validateActionState('startNextRound', 'scoring')) {
        return;
      }

      if (gameState.gameOver) {
        throw new Error('Game is over, cannot start next round');
      }

      gameService.startNextRound();
    } catch (error) {
      handleActionError('startNextRound', error);
      if (throwOnError) throw error;
    }
  }, [logAction, validateActionState, gameState.gameOver, handleActionError, throwOnError]);

  // Recovery Actions
  const triggerRecovery = useCallback(async (errorType?: string): Promise<ErrorRecoveryResult> => {
    try {
      logAction('triggerRecovery', { errorType });
      return await serviceIntegration.triggerRecovery(errorType);
    } catch (error) {
      handleActionError('triggerRecovery', error);
      throw error;
    }
  }, [logAction, handleActionError]);

  const emergencyReset = useCallback(async () => {
    try {
      logAction('emergencyReset');
      await serviceIntegration.emergencyReset();
    } catch (error) {
      handleActionError('emergencyReset', error);
      throw error;
    }
  }, [logAction, handleActionError]);

  // Utility Actions
  const refreshState = useCallback(() => {
    logAction('refreshState');
    // GameService automatically provides latest state, but we can force a health check
    serviceIntegration.getHealthStatus();
  }, [logAction]);

  const clearError = useCallback(() => {
    logAction('clearError');
    // This would need to be implemented in GameService if needed
    // For now, errors typically clear on successful actions
  }, [logAction]);

  // Memoize the complete actions object
  const actions = useMemo<GameActions>(() => ({
    connectToRoom,
    disconnectFromRoom,
    acceptRedeal,
    declineRedeal,
    makeDeclaration,
    playPieces,
    startNextRound,
    triggerRecovery,
    emergencyReset,
    refreshState,
    clearError
  }), [
    connectToRoom,
    disconnectFromRoom,
    acceptRedeal,
    declineRedeal,
    makeDeclaration,
    playPieces,
    startNextRound,
    triggerRecovery,
    emergencyReset,
    refreshState,
    clearError
  ]);

  return actions;
}

/**
 * Hook for accessing phase-specific actions
 * Returns only actions relevant to the current phase
 */
export function usePhaseActions(): Partial<GameActions> {
  const gameState = useGameState();
  const allActions = useGameActions();

  return useMemo(() => {
    const baseActions = {
      triggerRecovery: allActions.triggerRecovery,
      emergencyReset: allActions.emergencyReset,
      refreshState: allActions.refreshState,
      clearError: allActions.clearError
    };

    switch (gameState.phase) {
      case 'waiting':
        return {
          ...baseActions,
          connectToRoom: allActions.connectToRoom
        };

      case 'preparation':
        return {
          ...baseActions,
          acceptRedeal: allActions.acceptRedeal,
          declineRedeal: allActions.declineRedeal,
          disconnectFromRoom: allActions.disconnectFromRoom
        };

      case 'declaration':
        return {
          ...baseActions,
          makeDeclaration: allActions.makeDeclaration,
          disconnectFromRoom: allActions.disconnectFromRoom
        };

      case 'turn':
        return {
          ...baseActions,
          playPieces: allActions.playPieces,
          disconnectFromRoom: allActions.disconnectFromRoom
        };

      case 'scoring':
        return {
          ...baseActions,
          startNextRound: allActions.startNextRound,
          disconnectFromRoom: allActions.disconnectFromRoom
        };

      default:
        return baseActions;
    }
  }, [gameState.phase, allActions]);
}

/**
 * Hook for checking if specific actions are available
 */
export function useActionAvailability() {
  const gameState = useGameState();

  return useMemo(() => ({
    canAcceptRedeal: gameState.phase === 'preparation' && 
                     gameState.isMyDecision &&
                     gameState.isConnected && !gameState.error,
    
    canDeclineRedeal: gameState.phase === 'preparation' && 
                      gameState.isMyDecision &&
                      gameState.isConnected && !gameState.error,
    
    canMakeDeclaration: gameState.phase === 'declaration' && 
                        gameState.isMyTurn &&
                        gameState.isConnected && !gameState.error,
    
    canPlayPieces: gameState.phase === 'turn' && 
                   gameState.isMyTurn &&
                   gameState.myHand.length > 0 &&
                   gameState.isConnected && !gameState.error,
    
    canStartNextRound: gameState.phase === 'scoring' && 
                       !gameState.gameOver &&
                       gameState.isConnected && !gameState.error,
    
    canConnect: !gameState.isConnected,
    
    canDisconnect: gameState.isConnected,
    
    needsRecovery: gameState.error !== null || !gameState.isConnected
  }), [gameState]);
}

export default useGameActions;