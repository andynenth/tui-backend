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
import { useGameState } from '../hooks/useGameState';
import { useGameActions } from '../hooks/useGameActions';
import { useConnectionStatus } from '../hooks/useConnectionStatus';
import { serviceIntegration } from '../services/ServiceIntegration';

// Import components
import { GameContainer } from '../components/game/GameContainer';
import { Layout, Button, Modal, LoadingOverlay } from '../components';
import { ErrorBoundary } from '../components/ErrorBoundary';

const GamePageNew = () => {
  const navigate = useNavigate();
  const { roomId } = useParams();
  
  // New service-based state management
  const gameState = useGameState();
  const gameActions = useGameActions();
  const connectionStatus = useConnectionStatus(roomId);
  
  const [showLeaveModal, setShowLeaveModal] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);

  // Initialize services and connect to room
  useEffect(() => {
    const initializeGame = async () => {
      try {
        // Get player name from URL params or session storage
        const playerName = sessionStorage.getItem('playerName') || 'Player';
        
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
  }, [roomId, navigate]);

  // Handle game completion
  useEffect(() => {
    if (gameState.gameOver && gameState.winners.length > 0) {
      // Show game results
      const winnerText = gameState.winners.length === 1 
        ? `Winner: ${gameState.winners[0]}` 
        : `Winners: ${gameState.winners.join(', ')}`;
        
      // Could show a modal instead of alert
      alert(`Game ended! ${winnerText}`);
      
      // Navigate back to lobby after a delay
      setTimeout(() => {
        navigate('/lobby');
      }, 3000);
    }
  }, [gameState.gameOver, gameState.winners, navigate]);

  // Handle critical connection errors
  useEffect(() => {
    if (connectionStatus.error && !connectionStatus.isConnecting) {
      console.error('Critical connection error:', connectionStatus.error);
      // Could show error modal or redirect to lobby
    }
  }, [connectionStatus.error, connectionStatus.isConnecting]);

  const leaveGame = async () => {
    try {
      await gameActions.disconnectFromRoom();
      navigate('/lobby');
    } catch (error) {
      console.error('Error leaving game:', error);
      // Force navigation even if disconnect fails
      navigate('/lobby');
    }
  };

  const getPhaseDisplayName = (phase) => {
    const names = {
      waiting: 'Waiting',
      preparation: 'Preparation',
      declaration: 'Declaration',
      turn: 'Turn Play',
      scoring: 'Scoring'
    };
    return names[phase] || phase;
  };

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
      <Layout
        title={`Game - Room ${roomId}`}
        showConnection={true}
        connectionProps={{
          isConnected: connectionStatus.isConnected,
          isConnecting: connectionStatus.isConnecting,
          isReconnecting: connectionStatus.isReconnecting,
          error: connectionStatus.error,
          roomId
        }}
        headerContent={
          <div className="flex items-center space-x-4">
            {/* Current phase indicator */}
            <div className="text-sm">
              <span className="text-gray-600">Phase: </span>
              <span className="font-medium text-blue-600">
                {getPhaseDisplayName(gameState.phase)}
              </span>
            </div>

            {/* Player info */}
            <div className="text-sm text-gray-600">
              {gameState.playerName}
            </div>

            {/* Round info */}
            {gameState.currentRound && (
              <div className="text-sm text-gray-600">
                Round {gameState.currentRound}
              </div>
            )}

            {/* Leave game button */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowLeaveModal(true)}
            >
              Leave Game
            </Button>
          </div>
        }
      >
        {/* Full-screen game container */}
        <div className="h-full">
          <GameContainer roomId={roomId} />
        </div>

        {/* Connection status overlay */}
        {!connectionStatus.isConnected && !connectionStatus.isConnecting && (
          <div className="fixed bottom-4 right-4 bg-yellow-500 text-white px-4 py-2 rounded-lg shadow-lg">
            <div className="flex items-center">
              <span className="mr-2">⚠️</span>
              <span>Connection lost. Retrying...</span>
            </div>
          </div>
        )}

        {/* Game error overlay */}
        {gameState.error && (
          <div className="fixed top-4 right-4 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg max-w-sm">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <span className="mr-2">❌</span>
                <span className="text-sm">{gameState.error}</span>
              </div>
              <button
                onClick={() => gameActions.triggerRecovery()}
                className="ml-2 text-xs underline hover:no-underline"
              >
                Retry
              </button>
            </div>
          </div>
        )}
      </Layout>

      {/* Leave game confirmation */}
      <Modal
        isOpen={showLeaveModal}
        onClose={() => setShowLeaveModal(false)}
        title="Leave Game"
        size="sm"
      >
        <div className="space-y-4">
          <p className="text-gray-600">
            Are you sure you want to leave the game? 
            Your progress will be lost and other players will be notified.
          </p>
          
          <div className="flex space-x-3">
            <Button
              variant="danger"
              fullWidth
              onClick={leaveGame}
            >
              Leave Game
            </Button>
            <Button
              variant="ghost"
              fullWidth
              onClick={() => setShowLeaveModal(false)}
            >
              Stay in Game
            </Button>
          </div>
        </div>
      </Modal>
    </ErrorBoundary>
  );
};

export default GamePageNew;