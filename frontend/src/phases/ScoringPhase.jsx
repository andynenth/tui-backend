// frontend/src/phases/ScoringPhase.jsx

import React, { useState, useEffect } from 'react';
import { useGame } from '../contexts/GameContext';
import { Button } from '../components';

const ScoringPhase = () => {
  const game = useGame();
  const [roundScores, setRoundScores] = useState({});
  const [scoreBreakdown, setScoreBreakdown] = useState({});
  const [isGameComplete, setIsGameComplete] = useState(false);
  const [winner, setWinner] = useState(null);

  // Listen for score updates
  useEffect(() => {
    // This would normally come from the game state manager
    // For now, we'll calculate based on declarations vs actual
    calculateScores();
  }, [game.declarations, game.gameState]);

  const calculateScores = () => {
    // This is a simplified version - the real calculation 
    // would come from the backend/game state manager
    const declarations = game.declarations || {};
    const players = Object.keys(game.scores || {});
    
    const scores = {};
    const breakdown = {};
    
    players.forEach(player => {
      const declared = declarations[player] || 0;
      // In a real implementation, actual would come from turn results
      const actual = Math.floor(Math.random() * 4); // Placeholder
      
      let roundScore = 0;
      let multiplier = 1;
      
      if (declared === actual) {
        // Exact match
        roundScore = 10 + (declared * 2);
      } else {
        // Missed by some amount
        const difference = Math.abs(declared - actual);
        roundScore = Math.max(0, 5 - difference);
      }
      
      // Apply multipliers for special cases
      if (declared === 0 && actual === 0) {
        multiplier = 2; // Successful zero declaration
      }
      
      scores[player] = roundScore * multiplier;
      breakdown[player] = {
        declared,
        actual,
        base: roundScore,
        multiplier,
        total: scores[player]
      };
    });
    
    setRoundScores(scores);
    setScoreBreakdown(breakdown);
    
    // Check for game winner
    const totalScores = game.scores || {};
    const maxScore = Math.max(...Object.values(totalScores));
    if (maxScore >= 50) {
      setIsGameComplete(true);
      setWinner(Object.keys(totalScores).find(p => totalScores[p] === maxScore));
    }
  };

  const continueToNextRound = () => {
    game.actions.sendReady();
  };

  const renderScoreBreakdown = () => {
    return (
      <div className="space-y-4 max-w-2xl mx-auto">
        {Object.entries(scoreBreakdown).map(([player, breakdown]) => (
          <div 
            key={player}
            className={`border rounded-lg p-4 ${
              player === game.playerName 
                ? 'bg-blue-50 border-blue-200' 
                : 'bg-gray-50 border-gray-200'
            }`}
          >
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold text-gray-900">
                {player} {player === game.playerName && '(You)'}
              </h4>
              <div className="text-2xl font-bold text-blue-600">
                +{breakdown.total}
              </div>
            </div>
            
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Declared:</span>
                <span className="font-medium">{breakdown.declared} piles</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Actual:</span>
                <span className="font-medium">{breakdown.actual} piles</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Base score:</span>
                <span className="font-medium">{breakdown.base}</span>
              </div>
              {breakdown.multiplier > 1 && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Multiplier:</span>
                  <span className="font-medium text-green-600">×{breakdown.multiplier}</span>
                </div>
              )}
              <hr className="border-gray-300" />
              <div className="flex justify-between font-semibold">
                <span>Round score:</span>
                <span className="text-blue-600">+{breakdown.total}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderTotalScores = () => {
    const totalScores = { ...game.scores };
    
    // Add round scores to totals
    Object.entries(roundScores).forEach(([player, roundScore]) => {
      totalScores[player] = (totalScores[player] || 0) + roundScore;
    });

    const sortedPlayers = Object.entries(totalScores)
      .sort(([,a], [,b]) => b - a);

    return (
      <div className="max-w-md mx-auto">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 text-center">
          Total Scores
        </h3>
        
        <div className="space-y-2">
          {sortedPlayers.map(([player, score], index) => (
            <div 
              key={player}
              className={`flex items-center justify-between p-3 rounded-lg ${
                index === 0 ? 'bg-yellow-100 border-2 border-yellow-300' : 'bg-gray-100'
              }`}
            >
              <div className="flex items-center space-x-2">
                {index === 0 && <span className="text-xl">👑</span>}
                <span className={`font-medium ${
                  player === game.playerName ? 'text-blue-600' : 'text-gray-900'
                }`}>
                  {player} {player === game.playerName && '(You)'}
                </span>
              </div>
              <span className="text-xl font-bold">
                {score}
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderGameComplete = () => {
    if (!isGameComplete) return null;

    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-8">
        <div className="text-center">
          <h3 className="text-2xl font-bold text-green-800 mb-2">
            🎉 Game Complete! 🎉
          </h3>
          <p className="text-green-700 text-lg">
            Winner: <strong>{winner}</strong>
          </p>
          {winner === game.playerName && (
            <p className="text-green-600 mt-2">Congratulations! You won!</p>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="p-6">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Scoring Phase
        </h2>
        <p className="text-gray-600">
          Round complete! Here are the results and scores.
        </p>
      </div>

      {/* Game completion banner */}
      {renderGameComplete()}

      {/* Round score breakdown */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 text-center">
          Round {game.gameState?.currentRound || 1} Results
        </h3>
        {renderScoreBreakdown()}
      </div>

      {/* Total scores */}
      <div className="mb-8">
        {renderTotalScores()}
      </div>

      {/* Continue button */}
      <div className="text-center">
        {isGameComplete ? (
          <Button
            variant="success"
            size="lg"
            onClick={() => window.location.href = '/lobby'}
          >
            Return to Lobby
          </Button>
        ) : (
          <div className="space-y-2">
            <Button
              variant="primary"
              size="lg"
              onClick={continueToNextRound}
            >
              Ready for Next Round
            </Button>
            <p className="text-sm text-gray-500">
              Waiting for all players to be ready...
            </p>
          </div>
        )}
      </div>

      {/* Scoring rules reminder */}
      <div className="mt-8 bg-gray-50 rounded-lg p-4">
        <h4 className="font-medium text-gray-900 mb-2">Scoring Rules:</h4>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>• Exact match: 10 + (declared × 2) points</li>
          <li>• Missed by 1: 4 points</li>
          <li>• Missed by 2: 3 points</li>
          <li>• Missed by 3+: 0 points</li>
          <li>• Successful zero declaration: ×2 multiplier</li>
          <li>• First to 50 points wins!</li>
        </ul>
      </div>

      {/* Game state info */}
      <div className="mt-8 text-center text-sm text-gray-500">
        <p>
          Phase: Scoring • 
          Round: {game.gameState?.currentRound || 1} • 
          Room: {game.roomId}
        </p>
      </div>
    </div>
  );
};

export default ScoringPhase;