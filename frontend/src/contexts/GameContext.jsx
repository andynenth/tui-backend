// frontend/src/contexts/GameContext.jsx
// Simplified Phase 1-4 Enterprise Architecture Context

import React, { createContext, useContext, useState, useEffect } from 'react';

// Phase 5 unified state management
import { gameStore } from '../stores/UnifiedGameStore';
import { networkService } from '../services/NetworkService';

const GameContext = createContext(null);

export const useGame = () => {
  const context = useContext(GameContext);
  if (!context) {
    throw new Error('useGame must be used within a GameProvider');
  }
  return context;
};

export const GameProvider = ({
  children,
  roomId,
  playerName,
  initialData = {}
}) => {
  const [isInitialized, setIsInitialized] = useState(false);
  const [error, setError] = useState(null);
  const [gameState, setGameState] = useState(null);

  // Initialize Phase 5 Unified State Management
  useEffect(() => {
    const initializeGame = () => {
      try {
        if (roomId && playerName) {
          console.log('🚀 GAME_CONTEXT: Phase 5 Unified State Management initializing');
          
          // Set player info in unified store
          gameStore.setState({ roomId, playerName });
          
          // Subscribe to unified game store changes
          const unsubscribe = gameStore.subscribe((state) => {
            setGameState(state.gameState);
          });
          
          // Get initial state
          setGameState(gameStore.getState().gameState);
          setIsInitialized(true);
          
          return unsubscribe;
        } else {
          throw new Error('Missing room/player data');
        }
      } catch (err) {
        console.error('Failed to initialize GameContext:', err);
        setError(err.message);
      }
    };

    if (roomId && playerName) {
      const cleanup = initializeGame();
      return cleanup;
    }
  }, [roomId, playerName]);

  // Provide simple context value focused on Phase 5 unified state
  const contextValue = {
    // Basic state
    isInitialized,
    error,
    playerName,
    roomId,
    
    // Game state from unified store
    gameState,
    
    // Current phase from game state
    currentPhase: gameState?.phase || 'waiting',
    
    // Connection status from unified store
    isConnected: gameStore.getState().connectionStatus.isConnected,
    
    // Simple action methods that delegate to network service
    actions: {
      leaveGame: () => networkService.disconnectFromRoom(roomId),
    },
    
    // Legacy compatibility properties (simplified)
    myHand: gameState?.myHand || [],
    scores: gameState?.totalScores || {},
    isMyTurn: gameState?.isMyTurn || false,
  };

  return (
    <GameContext.Provider value={contextValue}>
      {children}
    </GameContext.Provider>
  );
};