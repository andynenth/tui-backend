// frontend/src/phases/TurnPhase.jsx

import React, { useState, useEffect } from 'react';
import { useGame } from '../contexts/GameContext';
import { Button, GamePiece } from '../components';

const TurnPhase = () => {
  const game = useGame();
  const [selectedPieces, setSelectedPieces] = useState([]);
  const [requiredPieceCount, setRequiredPieceCount] = useState(null);
  const [isMyTurn, setIsMyTurn] = useState(false);
  const [turnStarter, setTurnStarter] = useState(null);

  // Check turn state
  useEffect(() => {
    if (game.gameState?.manager) {
      const myTurnToPlay = game.gameState.manager.isMyTurnToPlay();
      setIsMyTurn(myTurnToPlay);
      
      // Get required piece count (set by first player)
      setRequiredPieceCount(game.gameState.manager.requiredPieceCount);
      
      // Get turn starter
      setTurnStarter(game.gameState.manager.currentTurnStarter);
    }
  }, [game.gameState?.manager, game.currentTurnPlays]);

  // Handle piece selection
  const togglePieceSelection = (pieceIndex) => {
    setSelectedPieces(prev => {
      if (prev.includes(pieceIndex)) {
        return prev.filter(i => i !== pieceIndex);
      } else {
        return [...prev, pieceIndex];
      }
    });
  };

  // Clear selection
  const clearSelection = () => {
    setSelectedPieces([]);
  };

  // Play selected pieces
  const playPieces = () => {
    if (selectedPieces.length === 0) return;
    
    // Validate piece count
    if (requiredPieceCount && selectedPieces.length !== requiredPieceCount) {
      alert(`You must play exactly ${requiredPieceCount} pieces`);
      return;
    }

    // First player sets the piece count
    if (!requiredPieceCount && game.gameState?.manager.isFirstPlayerInTurn()) {
      if (selectedPieces.length < 1 || selectedPieces.length > 6) {
        alert('You must play between 1 and 6 pieces');
        return;
      }
    }

    game.actions.playPieces(selectedPieces);
    setSelectedPieces([]);
  };

  // Get turn order and plays
  const getTurnInfo = () => {
    const turnPlays = game.currentTurnPlays || [];
    const turnProgress = game.gameState?.manager?.getTurnProgress() || { played: 0, total: 0 };
    
    return {
      plays: turnPlays,
      progress: turnProgress,
      isComplete: turnProgress.played >= turnProgress.total
    };
  };

  const renderHand = () => {
    if (!game.myHand || game.myHand.length === 0) {
      return (
        <div className="text-center py-8">
          <div className="text-gray-500">No pieces in hand</div>
        </div>
      );
    }

    return (
      <div className="grid grid-cols-4 gap-3 max-w-2xl mx-auto">
        {game.myHand.map((piece, index) => (
          <GamePiece
            key={index}
            piece={piece}
            size="lg"
            isSelected={selectedPieces.includes(index)}
            isPlayable={isMyTurn}
            onSelect={() => isMyTurn && togglePieceSelection(index)}
          />
        ))}
      </div>
    );
  };

  const renderTurnPlays = () => {
    const turnInfo = getTurnInfo();
    
    if (turnInfo.plays.length === 0) {
      return (
        <div className="text-center text-gray-500">
          No plays yet this turn
        </div>
      );
    }

    return (
      <div className="space-y-3">
        {turnInfo.plays.map((play, index) => (
          <div key={index} className="bg-gray-50 rounded-lg p-3">
            <div className="font-medium text-sm mb-2">
              {play.player} {play.player === game.playerName && '(You)'}:
            </div>
            <div className="flex flex-wrap gap-2">
              {play.cards.map((piece, pieceIndex) => (
                <GamePiece
                  key={pieceIndex}
                  piece={piece}
                  size="sm"
                  isPlayable={false}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderPlayActions = () => {
    if (!isMyTurn) return null;

    const isFirstPlayer = !requiredPieceCount && game.gameState?.manager?.isFirstPlayerInTurn();
    const canPlay = selectedPieces.length > 0;
    const pieceCountValid = isFirstPlayer 
      ? selectedPieces.length >= 1 && selectedPieces.length <= 6
      : !requiredPieceCount || selectedPieces.length === requiredPieceCount;

    return (
      <div className="space-y-4">
        <div className="text-center">
          {isFirstPlayer ? (
            <p className="text-sm text-blue-600 font-medium">
              You start this turn! Choose 1-6 pieces to play.
            </p>
          ) : (
            <p className="text-sm text-blue-600 font-medium">
              Your turn! Play {requiredPieceCount} piece{requiredPieceCount > 1 ? 's' : ''}.
            </p>
          )}
        </div>

        <div className="flex justify-center space-x-4">
          <Button
            variant="primary"
            onClick={playPieces}
            disabled={!canPlay || !pieceCountValid}
          >
            Play {selectedPieces.length} Piece{selectedPieces.length !== 1 ? 's' : ''}
          </Button>
          
          <Button
            variant="ghost"
            onClick={clearSelection}
            disabled={selectedPieces.length === 0}
          >
            Clear Selection
          </Button>
        </div>

        {selectedPieces.length > 0 && !pieceCountValid && (
          <div className="text-center text-red-600 text-sm">
            {isFirstPlayer 
              ? 'Select between 1 and 6 pieces'
              : `You must select exactly ${requiredPieceCount} pieces`
            }
          </div>
        )}
      </div>
    );
  };

  const turnInfo = getTurnInfo();

  return (
    <div className="p-6">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Turn Phase
        </h2>
        <p className="text-gray-600">
          Players take turns playing pieces. Highest total wins all pieces.
        </p>
      </div>

      {/* Turn progress */}
      <div className="text-center mb-6">
        <div className="inline-flex items-center bg-blue-50 border border-blue-200 rounded-lg px-4 py-2">
          <span className="text-sm text-blue-700">
            Turn {game.gameState?.currentTurnNumber || 1} • 
            Starter: {turnStarter} • 
            Plays: {turnInfo.progress.played}/{turnInfo.progress.total}
          </span>
        </div>
      </div>

      {/* Current turn plays */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 text-center">
          Turn Plays
        </h3>
        <div className="max-w-2xl mx-auto">
          {renderTurnPlays()}
        </div>
      </div>

      {/* Player's hand */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 text-center">
          Your Hand ({game.myHand?.length || 0} pieces)
          {selectedPieces.length > 0 && (
            <span className="text-blue-600 ml-2">
              ({selectedPieces.length} selected)
            </span>
          )}
        </h3>
        {renderHand()}
      </div>

      {/* Play actions */}
      {renderPlayActions()}

      {/* Waiting message */}
      {!isMyTurn && !turnInfo.isComplete && (
        <div className="text-center text-gray-600">
          <p>Waiting for other players to play...</p>
        </div>
      )}

      {/* Turn complete */}
      {turnInfo.isComplete && (
        <div className="text-center">
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 inline-block">
            <p className="text-green-800 font-medium">
              Turn complete! Determining winner...
            </p>
          </div>
        </div>
      )}

      {/* Game state info */}
      <div className="mt-8 text-center text-sm text-gray-500">
        <p>
          Phase: Turn • 
          Round: {game.gameState?.currentRound || 1} • 
          Required pieces: {requiredPieceCount || 'TBD'} • 
          Room: {game.roomId}
        </p>
      </div>
    </div>
  );
};

export default TurnPhase;