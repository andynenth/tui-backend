// frontend/src/pages/GamePage.jsx

import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useGame } from '../contexts/GameContext';
import { Layout, Button, Modal, LoadingOverlay } from '../components';

// Game phase components (to be implemented)
import PreparationPhase from '../phases/PreparationPhase';
import DeclarationPhase from '../phases/DeclarationPhase';
import TurnPhase from '../phases/TurnPhase';
import ScoringPhase from '../phases/ScoringPhase';

const GamePage = () => {
  const navigate = useNavigate();
  const { roomId } = useParams();
  const game = useGame();
  
  const [showLeaveModal, setShowLeaveModal] = useState(false);
  const [gameError, setGameError] = useState(null);

  // Handle game errors
  useEffect(() => {
    if (game.error) {
      setGameError(game.error);
    }
  }, [game.error]);

  // Handle game completion
  useEffect(() => {
    const unsubscriber = game.gameState?.manager?.on('gameEnded', (data) => {
      // Show game results and navigate back to lobby
      alert(`Game ended! Winner: ${data.winner || 'None'}`);
      setTimeout(() => {
        navigate('/lobby');
      }, 2000);
    });

    return () => {
      if (unsubscriber) unsubscriber();
    };
  }, [game.gameState?.manager, navigate]);

  const leaveGame = () => {
    game.actions.leaveGame();
    navigate('/lobby');
  };

  const renderCurrentPhase = () => {
    if (!game.isInitialized) {
      return (
        <div className="text-center py-12">
          <div className="text-lg text-gray-600">Initializing game...</div>
        </div>
      );
    }

    switch (game.currentPhase) {
      case 'preparation':
      case 'redeal':
        return <PreparationPhase />;
      
      case 'declaration':
        return <DeclarationPhase />;
      
      case 'turn':
        return <TurnPhase />;
      
      case 'scoring':
        return <ScoringPhase />;
      
      default:
        return (
          <div className="text-center py-12">
            <div className="text-lg text-gray-600">
              Waiting for game phase: {game.currentPhase}
            </div>
          </div>
        );
    }
  };

  const getPhaseDisplayName = (phase) => {
    const names = {
      preparation: 'Preparation',
      redeal: 'Redeal',
      declaration: 'Declaration',
      turn: 'Turn Play',
      scoring: 'Scoring',
      waiting: 'Waiting'
    };
    return names[phase] || phase;
  };

  return (
    <>
      <Layout
        title={`Game - Room ${roomId}`}
        showConnection={true}
        connectionProps={{
          isConnected: game.isConnected,
          isConnecting: game.socket?.isConnecting,
          isReconnecting: game.socket?.isReconnecting,
          error: game.socket?.connectionError,
          roomId
        }}
        headerContent={
          <div className="flex items-center space-x-4">
            {/* Current phase indicator */}
            <div className="text-sm">
              <span className="text-gray-600">Phase: </span>
              <span className="font-medium text-blue-600">
                {getPhaseDisplayName(game.currentPhase)}
              </span>
            </div>

            {/* Player info */}
            <div className="text-sm text-gray-600">
              {game.playerName}
            </div>

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
        <div className="max-w-6xl mx-auto px-4 py-6">
          {/* Game status bar */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-6">
                {/* Current phase */}
                <div>
                  <div className="text-sm text-gray-500">Current Phase</div>
                  <div className="font-medium text-gray-900">
                    {getPhaseDisplayName(game.currentPhase)}
                  </div>
                </div>

                {/* Hand size */}
                <div>
                  <div className="text-sm text-gray-500">Your Hand</div>
                  <div className="font-medium text-gray-900">
                    {game.myHand?.length || 0} pieces
                  </div>
                </div>

                {/* Your turn indicator */}
                {game.isMyTurn && (
                  <div className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
                    Your Turn
                  </div>
                )}
              </div>

              {/* Scores */}
              <div className="flex items-center space-x-4">
                <div className="text-sm text-gray-500">Scores:</div>
                {Object.entries(game.scores || {}).map(([player, score]) => (
                  <div key={player} className="text-sm">
                    <span className={player === game.playerName ? 'font-bold' : ''}>
                      {player}: {score}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Phase content */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 min-h-[400px]">
            {renderCurrentPhase()}
          </div>

          {/* Connection status */}
          {!game.isConnected && (
            <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-center">
                <span className="text-yellow-600 mr-2">⚠️</span>
                <p className="text-yellow-800">
                  Connection lost. Attempting to reconnect...
                </p>
              </div>
            </div>
          )}

          {/* Game error */}
          {gameError && (
            <div className="mt-6 bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <span className="text-red-600 mr-2">❌</span>
                  <p className="text-red-800">
                    Game error: {gameError.message || gameError}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setGameError(null)}
                >
                  Dismiss
                </Button>
              </div>
            </div>
          )}
        </div>
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

      <LoadingOverlay
        isVisible={!game.isInitialized && !game.error}
        message="Loading game..."
        subtitle="Connecting to game server and initializing state"
      />
    </>
  );
};

export default GamePage;