// frontend/src/contexts/GameContext.jsx
// Enhanced to integrate with new service architecture while maintaining backward compatibility

import React, { createContext, useContext, useState, useEffect, useMemo } from 'react';
import { useGameState } from '../hooks/useGameState';
import { usePhaseManager } from '../hooks/usePhaseManager';
import { useSocket } from '../hooks/useSocket';

// New service integration
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
  initialData = {}
}) => {
  const [isInitialized, setIsInitialized] = useState(false);
  const [error, setError] = useState(null);
  const [useNewServices, setUseNewServices] = useState(false);
  const [newServiceState, setNewServiceState] = useState(null);

  // Memoize initialData to prevent unnecessary re-renders
  const memoizedInitialData = useMemo(() => initialData, [JSON.stringify(initialData)]);

  // Initialize core hooks with memoization to prevent re-creation
  const socket = useSocket(roomId);
  const gameState = useGameState(roomId, playerName, memoizedInitialData);
  
  // Memoize phaseManager to prevent constant recreation
  const stableGameStateManager = useMemo(() => gameState.manager, [gameState.manager]);
  const stableSocketManager = useMemo(() => socket.manager, [socket.manager]);
  const phaseManager = usePhaseManager(stableGameStateManager, stableSocketManager, null);

  // Check if new services are available and healthy
  useEffect(() => {
    try {
      const health = getServicesHealth();
      const servicesReady = health.overall.healthy && health.game.healthy;
      
      if (servicesReady && roomId && playerName) {
        console.log('🚀 GAME_CONTEXT: New services available, enabling hybrid mode');
        setUseNewServices(true);
        
        // Subscribe to new service state changes
        const newServiceCleanup = gameService.addListener((state) => {
          setNewServiceState(state);
        });
        
        // Get initial state
        setNewServiceState(gameService.getState());
        
        return newServiceCleanup;
      }
    } catch (error) {
      console.log('🔧 GAME_CONTEXT: New services not available, using legacy mode:', error.message);
      setUseNewServices(false);
    }
  }, [roomId, playerName]);

  // Wait for socket connection, then initialize (legacy system)
  useEffect(() => {
    if (!roomId || !playerName) return;
    if (isInitialized) return; // Prevent re-initialization
    if (useNewServices) return; // Skip if using new services
    if (!socket.isConnected) return; // Wait for socket to be connected

    console.log('🚀 GAME_CONTEXT: Socket connected, initializing legacy game context for room', roomId);
    
    try {
      setError(null);
      
      // Set up game event handlers
      const unsubscribers = setupGameEventHandlers();

      setIsInitialized(true);
      console.log('✅ GAME_CONTEXT: Legacy game context initialized successfully');

      // Cleanup function
      return () => {
        console.log('🧹 GAME_CONTEXT: Cleaning up legacy game context');
        unsubscribers.forEach(unsub => unsub());
      };
    } catch (err) {
      console.error('❌ GAME_CONTEXT: Failed to initialize legacy game:', err);
      setError(err);
    }
  }, [roomId, playerName, socket.isConnected, useNewServices]); // Wait for socket connection

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
          name,
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

  // Enhanced actions - use new services when available, fall back to legacy
  const actions = {
    // Declaration actions
    makeDeclaration: (value) => {
      console.log('🎯 GAME_ACTIONS: Making declaration:', value);
      if (useNewServices) {
        try {
          gameService.makeDeclaration(value);
        } catch (error) {
          console.warn('New service failed, falling back to legacy:', error);
          socket.send('declare', { player_name: playerName, declaration: value });
        }
      } else {
        socket.send('declare', { player_name: playerName, declaration: value });
      }
    },

    // Turn actions
    playPieces: (indices) => {
      if (useNewServices) {
        try {
          gameService.playPieces(indices);
        } catch (error) {
          console.warn('New service failed, falling back to legacy:', error);
          const pieces = gameState.removeFromHand(indices);
          socket.send('play_pieces', { player_name: playerName, pieces, indices });
        }
      } else {
        const pieces = gameState.removeFromHand(indices);
        socket.send('play_pieces', { player_name: playerName, pieces, indices });
      }
    },

    // Redeal actions
    requestRedeal: () => {
      socket.send('request_redeal', { player_name: playerName });
    },

    acceptRedeal: () => {
      if (useNewServices) {
        try {
          gameService.acceptRedeal();
        } catch (error) {
          console.warn('New service failed, falling back to legacy:', error);
          socket.send('accept_redeal', { player_name: playerName });
        }
      } else {
        socket.send('accept_redeal', { player_name: playerName });
      }
    },

    declineRedeal: () => {
      if (useNewServices) {
        try {
          gameService.declineRedeal();
        } catch (error) {
          console.warn('New service failed, falling back to legacy:', error);
          socket.send('decline_redeal', { player_name: playerName });
        }
      } else {
        socket.send('decline_redeal', { player_name: playerName });
      }
    },

    // General actions
    sendReady: () => {
      socket.send('player_ready', { player_name: playerName });
    },

    leaveGame: () => {
      if (useNewServices) {
        try {
          gameService.leaveRoom();
        } catch (error) {
          console.warn('New service failed, falling back to legacy:', error);
          socket.send('leave_game', { player_name: playerName });
          socket.disconnect();
        }
      } else {
        socket.send('leave_game', { player_name: playerName });
        socket.disconnect();
      }
    }
  };

  // Determine final state based on service availability
  const finalPhase = useNewServices && newServiceState ? newServiceState.phase : phaseManager?.currentPhaseName;
  const finalConnected = useNewServices && newServiceState ? newServiceState.isConnected : socket.isConnected;

  const value = {
    // State
    isInitialized: useNewServices ? (newServiceState?.isConnected || false) : isInitialized,
    error: useNewServices ? newServiceState?.error : error,
    roomId,
    playerName,

    // Core managers (legacy)
    socket,
    gameState,
    phaseManager,

    // Service information
    useNewServices,
    servicesHealth: useNewServices ? getServicesHealth() : null,

    // Computed state (hybrid - prefer new services)
    isConnected: finalConnected,
    currentPhase: finalPhase,
    myHand: useNewServices && newServiceState ? newServiceState.myHand : gameState?.myHand,
    declarations: useNewServices && newServiceState ? newServiceState.declarations : gameState?.declarations,
    scores: useNewServices && newServiceState ? newServiceState.totalScores : gameState?.scores,
    isMyTurn: useNewServices && newServiceState ? newServiceState.isMyTurn : gameState?.isMyTurn,

    // Additional new service state (when available)
    ...(useNewServices && newServiceState && {
      players: newServiceState.players,
      weakHands: newServiceState.weakHands,
      redealMultiplier: newServiceState.redealMultiplier,
      currentRound: newServiceState.currentRound,
      gameOver: newServiceState.gameOver,
      winners: newServiceState.winners
    }),

    // Actions
    actions
  };

  return (
    <GameContext.Provider value={value}>
      {children}
    </GameContext.Provider>
  );
};