// frontend/src/contexts/GameContext.jsx

import React, { createContext, useContext, useState, useEffect, useMemo } from 'react';
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

  // Memoize initialData to prevent unnecessary re-renders
  const memoizedInitialData = useMemo(() => initialData, [JSON.stringify(initialData)]);

  // Initialize core hooks with memoization to prevent re-creation
  const socket = useSocket(roomId);
  const gameState = useGameState(roomId, playerName, memoizedInitialData);
  
  // Memoize phaseManager to prevent constant recreation
  const stableGameStateManager = useMemo(() => gameState.manager, [gameState.manager]);
  const stableSocketManager = useMemo(() => socket.manager, [socket.manager]);
  const phaseManager = usePhaseManager(stableGameStateManager, stableSocketManager, null);

  // Wait for socket connection, then initialize
  useEffect(() => {
    if (!roomId || !playerName) return;
    if (isInitialized) return; // Prevent re-initialization
    if (!socket.isConnected) return; // Wait for socket to be connected

    console.log('🚀 GAME_CONTEXT: Socket connected, initializing game context for room', roomId);
    
    try {
      setError(null);
      
      // Set up game event handlers
      const unsubscribers = setupGameEventHandlers();

      setIsInitialized(true);
      console.log('✅ GAME_CONTEXT: Game context initialized successfully');

      // Cleanup function
      return () => {
        console.log('🧹 GAME_CONTEXT: Cleaning up game context');
        unsubscribers.forEach(unsub => unsub());
      };
    } catch (err) {
      console.error('❌ GAME_CONTEXT: Failed to initialize game:', err);
      setError(err);
    }
  }, [roomId, playerName, socket.isConnected]); // Wait for socket connection

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
      console.log('🎯 GAME_CONTEXT: Received phase_change event:', data);
      
      // Update game state with player data if available
      if (data.players && gameState.manager) {
        const playerData = data.players[playerName];
        if (playerData && playerData.hand) {
          console.log('🃏 GAME_CONTEXT: Updating hand data:', playerData.hand);
          gameState.manager.updateHand(playerData.hand);
        }
      }
      
      // Update player list from phase_data if available
      if (data.phase_data && data.phase_data.declaration_order && gameState.manager) {
        const playerNames = data.phase_data.declaration_order;
        console.log('👥 GAME_CONTEXT: Updating player list:', playerNames);
        
        // Create player objects from names
        const players = playerNames.map(name => ({
          name: name,
          score: 0,
          is_bot: name !== playerName
        }));
        
        // Update GameStateManager players
        gameState.manager.players = players;
        console.log('👥 GAME_CONTEXT: GameStateManager now has', players.length, 'players');
      }
      
      if (phaseManager && data.phase) {
        const phaseName = data.phase.toLowerCase();
        console.log('🎯 GAME_CONTEXT: Transitioning to phase:', phaseName);
        await phaseManager.transitionTo(phaseName);
      } else {
        console.error('❌ GAME_CONTEXT: Invalid phase change data or no phase manager:', { data, phaseManager });
      }
    });
    unsubscribers.push(unsubPhaseChange);

    // Declaration events
    const unsubDeclaration = socket.on('player_declared', (data) => {
      gameState.addDeclaration(data.player, data.declaration);
    });
    unsubscribers.push(unsubDeclaration);

    // Declaration events (from bots)
    const unsubDeclare = socket.on('declare', (data) => {
      console.log('🎯 GAME_CONTEXT: Received declare event:', data);
      gameState.addDeclaration(data.player, data.value);
    });
    unsubscribers.push(unsubDeclare);

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
      console.log('🎯 GAME_ACTIONS: Making declaration:', value);
      socket.send('declare', { player_name: playerName, declaration: value });
    },

    // Turn actions
    playPieces: (indices) => {
      const pieces = gameState.removeFromHand(indices);
      socket.send('play_pieces', { player_name: playerName, pieces, indices });
    },

    // Redeal actions
    requestRedeal: () => {
      socket.send('request_redeal', { player_name: playerName });
    },

    acceptRedeal: () => {
      socket.send('accept_redeal', { player_name: playerName });
    },

    declineRedeal: () => {
      socket.send('decline_redeal', { player_name: playerName });
    },

    // General actions
    sendReady: () => {
      socket.send('player_ready', { player_name: playerName });
    },

    leaveGame: () => {
      socket.send('leave_game', { player_name: playerName });
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