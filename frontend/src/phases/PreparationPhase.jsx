// frontend/src/phases/PreparationPhase.jsx
// Enhanced for Phase 3 Task 3.2: Works with both legacy and new service architecture

import React, { useState, useEffect } from 'react';
import { useGame } from '../contexts/GameContext';
import { Button, GamePiece } from '../components';

const PreparationPhase = () => {
  const game = useGame();
  const [hasWeakHand, setHasWeakHand] = useState(false);
  const [redealRequested, setRedealRequested] = useState(false);

  // Check for weak hand (enhanced to work with both service types)
  useEffect(() => {
    if (!game.myHand || game.myHand.length === 0) return;

    // If using new services, use the computed state
    if (game.useNewServices && game.isMyHandWeak !== undefined) {
      setHasWeakHand(game.isMyHandWeak);
      return;
    }

    // Legacy calculation for backward compatibility
    const hasStrongPiece = game.myHand.some(piece => {
      // Handle both new service format and legacy format
      if (typeof piece === 'object' && piece.value) {
        return piece.value > 9; // New service format
      }
      // Parse point value from piece string (legacy format)
      const match = piece.match(/\((\d+)\)/);
      const points = match ? parseInt(match[1]) : 0;
      return points > 9;
    });

    setHasWeakHand(!hasStrongPiece);
  }, [game.myHand, game.useNewServices, game.isMyHandWeak]);

  const requestRedeal = () => {
    game.actions.requestRedeal();
    setRedealRequested(true);
  };

  const acceptRedeal = () => {
    game.actions.acceptRedeal();
  };

  const declineRedeal = () => {
    game.actions.declineRedeal();
  };

  const renderHand = () => {
    if (!game.myHand || game.myHand.length === 0) {
      return (
        <div className="text-center py-8">
          <div className="text-gray-500">Waiting for cards...</div>
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
            isPlayable={false}
          />
        ))}
      </div>
    );
  };

  return (
    <div className="p-6">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Preparation Phase
        </h2>
        <p className="text-gray-600">
          Cards have been dealt. Check your hand and decide if you want to request a redeal.
        </p>
      </div>

      {/* Player's hand */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 text-center">
          Your Hand ({game.myHand?.length || 0} pieces)
        </h3>
        {renderHand()}
      </div>

      {/* Weak hand detection */}
      {hasWeakHand && !redealRequested && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
          <div className="flex items-center">
            <span className="text-yellow-600 mr-2">⚠️</span>
            <div className="flex-1">
              <h4 className="font-medium text-yellow-800">Weak Hand Detected</h4>
              <p className="text-sm text-yellow-700 mt-1">
                You have no pieces worth more than 9 points. You can request a redeal.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Redeal actions */}
      <div className="text-center space-y-4">
        {!redealRequested ? (
          <div className="space-y-2">
            {hasWeakHand && (
              <Button
                variant="primary"
                size="lg"
                onClick={requestRedeal}
              >
                Request Redeal (Weak Hand)
              </Button>
            )}
            
            <Button
              variant="success"
              size="lg"
              onClick={() => game.actions.sendReady()}
            >
              Ready to Continue
            </Button>
            
            <p className="text-sm text-gray-500">
              {hasWeakHand 
                ? 'You can request a redeal or continue with your current hand'
                : 'Your hand looks good! Ready to continue?'
              }
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-blue-800 font-medium">
                Redeal requested. Waiting for other players to respond...
              </p>
            </div>
            
            <div className="flex justify-center space-x-4">
              <Button
                variant="success"
                onClick={acceptRedeal}
              >
                Accept Redeal
              </Button>
              
              <Button
                variant="danger"
                onClick={declineRedeal}
              >
                Decline Redeal
              </Button>
            </div>
            
            <p className="text-sm text-gray-500">
              All players must agree for a redeal to occur
            </p>
          </div>
        )}
      </div>

      {/* Game state info */}
      <div className="mt-8 text-center text-sm text-gray-500">
        <p>
          Phase: Preparation • 
          Players: {Object.keys(game.scores || {}).length} • 
          Room: {game.roomId}
        </p>
      </div>
    </div>
  );
};

export default PreparationPhase;