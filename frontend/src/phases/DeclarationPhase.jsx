// frontend/src/phases/DeclarationPhase.jsx

import React, { useState, useEffect } from 'react';
import { useGame } from '../contexts/GameContext';
import { Button, GamePiece } from '../components';

const DeclarationPhase = () => {
  const game = useGame();
  const [selectedDeclaration, setSelectedDeclaration] = useState(null);
  const [validOptions, setValidOptions] = useState([]);
  const [isMyTurn, setIsMyTurn] = useState(false);

  // Check if it's my turn to declare
  useEffect(() => {
    if (game.gameState?.manager) {
      const myTurnToDeclare = game.gameState.manager.isMyTurnToDeclare();
      setIsMyTurn(myTurnToDeclare);
      
      if (myTurnToDeclare) {
        // Calculate if I'm the last player to declare
        const totalPlayers = Object.keys(game.scores || {}).length;
        const declarationCount = Object.keys(game.declarations || {}).length;
        const isLastPlayer = declarationCount === totalPlayers - 1;
        
        const options = game.gameState.manager.getValidDeclarationOptions(isLastPlayer);
        setValidOptions(options);
      }
    }
  }, [game.gameState?.manager, game.declarations, game.scores]);

  const makeDeclaration = () => {
    if (selectedDeclaration !== null) {
      game.actions.makeDeclaration(selectedDeclaration);
      setSelectedDeclaration(null);
    }
  };

  const getDeclarationProgress = () => {
    if (!game.gameState?.manager) return { declared: 0, total: 0 };
    return game.gameState.manager.getDeclarationProgress();
  };

  const renderDeclarationOptions = () => {
    if (!isMyTurn) return null;

    const handSize = game.myHand?.length || 0;
    
    return (
      <div className="space-y-4">
        <h4 className="font-medium text-gray-900">
          Choose your declaration (0 to {handSize} piles):
        </h4>
        
        <div className="grid grid-cols-5 gap-2 max-w-md mx-auto">
          {validOptions.map(option => (
            <Button
              key={option}
              variant={selectedDeclaration === option ? 'primary' : 'outline'}
              onClick={() => setSelectedDeclaration(option)}
              className="aspect-square"
            >
              {option}
            </Button>
          ))}
        </div>

        {selectedDeclaration !== null && (
          <div className="text-center space-y-2">
            <p className="text-sm text-gray-600">
              You selected: <strong>{selectedDeclaration} piles</strong>
            </p>
            <Button
              variant="success"
              onClick={makeDeclaration}
            >
              Confirm Declaration
            </Button>
          </div>
        )}

        <div className="text-xs text-gray-500 max-w-md mx-auto">
          <p className="mb-1">Rules:</p>
          <ul className="list-disc list-inside space-y-1">
            <li>Declare how many piles you think you&apos;ll win</li>
            <li>Total declarations cannot equal 8 (if you&apos;re last player)</li>
            <li>If you declared 0 twice in a row, you must declare at least 1</li>
          </ul>
        </div>
      </div>
    );
  };

  const renderDeclarationStatus = () => {
    const progress = getDeclarationProgress();
    const declarations = game.declarations || {};
    
    return (
      <div className="space-y-4">
        <div className="text-center">
          <h4 className="font-medium text-gray-900 mb-2">
            Declaration Progress ({progress.declared}/{progress.total})
          </h4>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress.percentage}%` }}
            ></div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 max-w-md mx-auto">
          {Object.entries(declarations).map(([player, declaration]) => (
            <div 
              key={player}
              className={`p-3 rounded-lg border ${
                player === game.playerName 
                  ? 'bg-blue-50 border-blue-200' 
                  : 'bg-gray-50 border-gray-200'
              }`}
            >
              <div className="font-medium text-sm">
                {player} {player === game.playerName && '(You)'}
              </div>
              <div className="text-lg font-bold text-blue-600">
                {declaration} piles
              </div>
            </div>
          ))}
        </div>

        {!isMyTurn && progress.declared < progress.total && (
          <div className="text-center text-gray-600">
            <p>Waiting for other players to declare...</p>
          </div>
        )}
      </div>
    );
  };

  const calculateTotal = () => {
    const declarations = game.declarations || {};
    return Object.values(declarations).reduce((sum, val) => sum + (val || 0), 0);
  };

  const renderHand = () => {
    if (!game.myHand || game.myHand.length === 0) {
      return (
        <div className="text-center py-4">
          <div className="text-gray-500">No pieces in hand</div>
        </div>
      );
    }

    return (
      <div className="space-y-3">
        <h4 className="text-center font-medium text-gray-900">Your hand:</h4>
        <div className="grid grid-cols-4 gap-3 max-w-2xl mx-auto">
          {game.myHand.map((piece, index) => (
            <GamePiece
              key={index}
              piece={piece}
              size="md"
              isSelected={false}
              isPlayable={false}
              onSelect={() => {}} // No selection during declaration phase
            />
          ))}
        </div>
        <p className="text-center text-sm text-gray-600">
          {game.myHand.length} pieces total
        </p>
      </div>
    );
  };

  return (
    <div className="p-6">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Declaration Phase
        </h2>
        <p className="text-gray-600">
          Each player declares how many piles they expect to win this round.
        </p>
      </div>

      {/* Hand display */}
      <div className="mb-8">
        {renderHand()}
      </div>

      {/* Declaration interface */}
      <div className="max-w-2xl mx-auto">
        {isMyTurn ? renderDeclarationOptions() : renderDeclarationStatus()}
      </div>

      {/* Total declaration info */}
      {Object.keys(game.declarations || {}).length > 0 && (
        <div className="mt-8 text-center">
          <div className="inline-flex items-center bg-yellow-50 border border-yellow-200 rounded-lg px-4 py-2">
            <span className="text-sm text-yellow-700">
              Current total: <strong>{calculateTotal()}</strong> 
              {calculateTotal() === 8 && ' (Warning: Total cannot be 8!)'}
            </span>
          </div>
        </div>
      )}

      {/* Game state info */}
      <div className="mt-8 text-center text-sm text-gray-500">
        <p>
          Phase: Declaration • 
          Round: {game.gameState?.currentRound || 1} • 
          Room: {game.roomId}
        </p>
      </div>
    </div>
  );
};

export default DeclarationPhase;