// frontend/src/contexts/GameContext.jsx
// Simplified Phase 1-4 Enterprise Architecture Context

import React, { createContext, useContext, useState, useEffect } from 'react';

// Phase 1-4 service integration
import { gameService, getServicesHealth } from '../services';

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
  initialData = {},
}) => {
  const [isInitialized, setIsInitialized] = useState(false);
  const [error, setError] = useState(null);
  const [gameState, setGameState] = useState(null);

  // Initialize Phase 1-4 Enterprise Services
  useEffect(() => {
    const initializeGame = async () => {
      try {
        const health = getServicesHealth();

        if (health.overall.healthy && roomId && playerName) {
          console.log(
            '🚀 GAME_CONTEXT: Phase 1-4 Enterprise Architecture initializing'
          );

          // Subscribe to game service state changes
          const unsubscribe = gameService.addListener((state) => {
            setGameState(state);
          });

          // Get initial state
          setGameState(gameService.getState());
          setIsInitialized(true);

          return unsubscribe;
        } else {
          throw new Error(
            'Phase 1-4 services not healthy or missing room/player data'
          );
        }
      } catch (err) {
        console.error('Failed to initialize GameContext:', err);
        setError(err.message);
      }
    };

    if (roomId && playerName) {
      initializeGame();
    }
  }, [roomId, playerName]);

  // Provide simple context value focused on Phase 1-4 architecture
  const contextValue = {
    // Basic state
    isInitialized,
    error,
    playerName,
    roomId,

    // Game state from Phase 1-4 services
    gameState,

    // Current phase from game state
    currentPhase: gameState?.phase || 'waiting',

    // Connection status (from services)
    isConnected: getServicesHealth().network.healthy,

    // Simple action methods that delegate to services
    actions: {
      // Services handle the actual implementation
      leaveGame: () => gameService.disconnect(),
    },

    // Legacy compatibility properties (simplified)
    myHand: gameState?.hand || [],
    scores: gameState?.scores || {},
    isMyTurn: gameState?.currentPlayer === playerName,
  };

  return (
    <GameContext.Provider value={contextValue}>{children}</GameContext.Provider>
  );
};
