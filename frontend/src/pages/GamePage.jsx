/**
 * 🎮 **GamePage Component** - Updated Game Page with New Architecture
 *
 * Phase 2, Task 2.3: Smart Container Components
 *
 * Features:
 * ✅ Uses new GameContainer for game state management
 * ✅ Service integration for robust connection handling
 * ✅ Error boundary integration
 * ✅ Maintains compatibility with existing routing
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useApp } from '../contexts/AppContext';
import { useGameState } from '../hooks/useGameState';
import { useGameActions } from '../hooks/useGameActions';
import { useConnectionStatus } from '../hooks/useConnectionStatus';
import { serviceIntegration } from '../services/ServiceIntegration';
import { getSession, clearSession } from '../utils/sessionStorage';

// Import components
import { GameContainer } from '../components/game/GameContainer';
import { LoadingOverlay } from '../components';
import ErrorBoundary from '../components/ErrorBoundary';
import ToastContainer from '../components/ToastContainer';

const GamePage = () => {
  const navigate = useNavigate();
  const { roomId } = useParams();
  const app = useApp();

  // New service-based state management
  const gameState = useGameState();
  const gameActions = useGameActions();
  const connectionStatus = useConnectionStatus(roomId);

  const [isInitialized, setIsInitialized] = useState(false);

  // Initialize services and connect to room
  useEffect(() => {
    const initializeGame = async () => {
      try {
        // Get player name from AppContext
        const playerName = app.playerName;

        if (!playerName) {
          console.error('🎮 GAME: No player name found, redirecting to start page');
          navigate('/');
          return;
        }

        if (roomId) {
          console.log(`🎮 GAME: Initializing game for ${playerName} in room ${roomId}`);
          
          // Check if this is a session recovery
          const session = getSession();
          const isRecovery =
            session &&
            session.roomId === roomId &&
            session.playerName === playerName;

          if (isRecovery) {
            console.log(
              '🎮 GAME: Recovering session for',
              playerName,
              'in room',
              roomId
            );
          }

          // 🎯 FIX: Check if GameService is already connected to this room AND has game state
          const currentGameState = gameState;
          console.log('🎮 GAME: Current GameService state from useGameState hook:', {
            roomId: currentGameState.roomId,
            isConnected: currentGameState.isConnected,
            phase: currentGameState.phase,
            targetRoomId: roomId,
            playerName: currentGameState.playerName
          });
          
          // Check if we already have active game state (even if temporarily disconnected)
          const hasActiveGameState = currentGameState.roomId === roomId && 
                                    currentGameState.playerName === playerName &&
                                    currentGameState.phase !== 'waiting';
          
          const isCurrentlyConnected = currentGameState.isConnected;
          
          // 🎯 CRITICAL FIX: Skip connection entirely if we have the right room/player combo
          // This prevents the double connection issue that resets game state
          if (currentGameState.roomId === roomId && 
              currentGameState.playerName === playerName) {
            console.log('🎮 GAME: Already in correct room with correct player');
            console.log('🎮 GAME: Connection status:', isCurrentlyConnected);
            console.log('🎮 GAME: Current phase:', currentGameState.phase);
            setIsInitialized(true);
            
            // If disconnected but have the right room, just wait for auto-reconnect
            if (!isCurrentlyConnected) {
              console.log('🎮 GAME: Waiting for NetworkService auto-reconnect...');
            }
            return;
          }

          // Only connect if we're NOT already in the correct room
          console.log('🎮 GAME: Different room or player, need to connect');
          console.log('🎮 GAME: Connection decision factors:', {
            currentRoom: currentGameState.roomId,
            targetRoom: roomId,
            currentPlayer: currentGameState.playerName,
            targetPlayer: playerName,
            isConnected: currentGameState.isConnected
          });
          
          await serviceIntegration.connectToRoom(roomId, playerName);
          console.log('🎮 GAME: Service integration connection completed');
          setIsInitialized(true);
        }
      } catch (error) {
        console.error('🎮 GAME: Failed to initialize game:', error);
        // Could redirect back to lobby on critical errors
        if (error.message.includes('Room not found')) {
          console.log('🎮 GAME: Room not found, redirecting to lobby');
          navigate('/lobby');
        }
      }
    };

    initializeGame();

    // Cleanup on unmount - DON'T disconnect if just navigating within the same game
    return () => {
      // Only disconnect if navigating away from the game entirely
      const currentPath = window.location.pathname;
      const isLeavingGame = !currentPath.includes(`/game/${roomId}`);
      
      if (roomId && isLeavingGame) {
        console.log('🎮 GAME: Leaving game, disconnecting...');
        serviceIntegration.disconnectFromRoom().catch((err) => {
          console.error('Error disconnecting on unmount:', err);
        });
      } else {
        console.log('🎮 GAME: Staying in game, keeping connection');
      }
    };
  }, [roomId, navigate, app.playerName]);

  // Handle critical connection errors
  useEffect(() => {
    if (connectionStatus.error && !connectionStatus.isConnecting) {
      console.error('Critical connection error:', connectionStatus.error);
      // Could show error modal or redirect to lobby
    }
  }, [connectionStatus.error, connectionStatus.isConnecting]);

  // Show loading overlay during initialization
  if (!isInitialized && !gameState.error) {
    return (
      <LoadingOverlay
        isVisible={true}
        message="Connecting to game..."
        subtitle="Initializing game state and connecting to server"
      />
    );
  }

  return (
    <ErrorBoundary>
      <div className="game-page-wrapper">
        {/* Toast notifications for disconnect/reconnect events */}
        <ToastContainer position="top-right" maxToasts={5} />

        {/* GameContainer now handles all UI including layout */}
        <GameContainer
          roomId={roomId}
          onNavigateToLobby={() => navigate('/lobby')}
        />
      </div>
    </ErrorBoundary>
  );
};

export default GamePage;
