// frontend/src/contexts/GameContext.jsx

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useGameState } from '../hooks/useGameState';
import { usePhaseManager } from '../hooks/usePhaseManager';
import { useSocket } from '../hooks/useSocket';

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

  // Initialize core hooks
  const socket = useSocket(roomId);
  const gameState = useGameState(roomId, playerName, initialData);
  const phaseManager = usePhaseManager(gameState.manager, socket.manager, null);

  // Initialize connections and state
  useEffect(() => {
    if (!roomId || !playerName) return;

    const initialize = async () => {
      try {
        setError(null);
        
        // Wait for socket connection
        if (!socket.isConnected && !socket.isConnecting) {
          await socket.connect();
        }

        // Set up game event handlers
        const unsubscribers = setupGameEventHandlers();

        setIsInitialized(true);

        // Cleanup function
        return () => {
          unsubscribers.forEach(unsub => unsub());
        };
      } catch (err) {
        console.error('Failed to initialize game:', err);
        setError(err);
      }
    };

    initialize();
  }, [roomId, playerName, socket.isConnected]);

  // Set up game-specific event handlers
  const setupGameEventHandlers = () => {
    const unsubscribers = [];

    // Hand updates
    const unsubHandUpdate = socket.on('hand_update', (data) => {
      gameState.updateHand(data.hand);
    });
    unsubscribers.push(unsubHandUpdate);

    // Phase transitions
    const unsubPhaseChange = socket.on('phase_change', async (data) => {
      await phaseManager.transitionTo(data.phase.toLowerCase());
    });
    unsubscribers.push(unsubPhaseChange);

    // Declaration events
    const unsubDeclaration = socket.on('player_declared', (data) => {
      gameState.addDeclaration(data.player, data.declaration);
    });
    unsubscribers.push(unsubDeclaration);

    // Turn events
    const unsubTurnStart = socket.on('turn_started', (data) => {
      gameState.startNewTurn(data.starter);
    });
    unsubscribers.push(unsubTurnStart);

    const unsubPlayMade = socket.on('play_made', (data) => {
      gameState.addTurnPlay(data.player, data.cards);
    });
    unsubscribers.push(unsubPlayMade);

    // Score updates
    const unsubScore = socket.on('score_update', (data) => {
      Object.entries(data.scores).forEach(([player, score]) => {
        gameState.updateScore(player, score);
      });
    });
    unsubscribers.push(unsubScore);

    // Round events
    const unsubNewRound = socket.on('new_round', (data) => {
      gameState.startNewRound(data);
    });
    unsubscribers.push(unsubNewRound);

    // Game end
    const unsubGameEnd = socket.on('game_ended', (data) => {
      gameState.endGame(data);
    });
    unsubscribers.push(unsubGameEnd);

    return unsubscribers;
  };

  // Game actions
  const actions = {
    // Declaration actions
    makeDeclaration: (value) => {
      socket.send('declare', { declaration: value });
    },

    // Turn actions
    playPieces: (indices) => {
      const pieces = gameState.removeFromHand(indices);
      socket.send('play_pieces', { pieces, indices });
    },

    // Redeal actions
    requestRedeal: () => {
      socket.send('request_redeal');
    },

    acceptRedeal: () => {
      socket.send('accept_redeal');
    },

    declineRedeal: () => {
      socket.send('decline_redeal');
    },

    // General actions
    sendReady: () => {
      socket.send('player_ready');
    },

    leaveGame: () => {
      socket.send('leave_game');
      socket.disconnect();
    }
  };

  const value = {
    // State
    isInitialized,
    error,
    roomId,
    playerName,

    // Core managers
    socket,
    gameState,
    phaseManager,

    // Computed state
    isConnected: socket.isConnected,
    currentPhase: phaseManager.currentPhaseName,
    myHand: gameState.myHand,
    declarations: gameState.declarations,
    scores: gameState.scores,
    isMyTurn: gameState.isMyTurn,

    // Actions
    actions
  };

  return (
    <GameContext.Provider value={value}>
      {children}
    </GameContext.Provider>
  );
};