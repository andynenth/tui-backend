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

// Import components
import { GameContainer } from '../components/game/GameContainer';
import { LoadingOverlay } from '../components';
import ErrorBoundary from '../components/ErrorBoundary';

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
          console.error('No player name found, redirecting to start page');
          navigate('/');
          return;
        }
        
        if (roomId) {
          await serviceIntegration.connectToRoom(roomId, playerName);
          setIsInitialized(true);
        }
      } catch (error) {
        console.error('Failed to initialize game:', error);
        // Could redirect back to lobby on critical errors
        if (error.message.includes('Room not found')) {
          navigate('/lobby');
        }
      }
    };

    initializeGame();

    // Cleanup on unmount
    return () => {
      if (roomId) {
        serviceIntegration.disconnectFromRoom().catch(err => {
          console.error('Error disconnecting on unmount:', err);
        });
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