/**
 * 🏆 **ScoringUI Component** - Pure Scoring Phase Interface
 * 
 * Phase 2, Task 2.2: Pure UI Components
 * 
 * Features:
 * ✅ Pure functional component (props in, JSX out)
 * ✅ No hooks except local UI state
 * ✅ Comprehensive prop interfaces
 * ✅ Accessible and semantic HTML
 * ✅ Tailwind CSS styling
 */

import React from 'react';
import PropTypes from 'prop-types';
import { PlayerSlot } from '../PlayerSlot';
import { Button } from '../Button';

/**
 * Pure UI component for scoring phase
 */
export function ScoringUI({
  // Data props (all calculated by backend)
  players = [],
  roundScores = {},
  totalScores = {},
  redealMultiplier = 1,
  playersWithScores = [], // backend provides sorted players with all calculated data
  
  // State props
  gameOver = false,
  winners = [],
  
  // Action props
  onStartNextRound,
  onEndGame
}) {
  const hasWinners = winners.length > 0;
  // Use backend-provided sorted players, or fallback to manual sort if needed
  const sortedPlayers = playersWithScores.length > 0 ? playersWithScores : 
    players.map(player => ({
      ...player,
      roundScore: roundScores[player.name] || 0,
      totalScore: totalScores[player.name] || 0,
      isWinner: winners.includes(player.name)
    })).sort((a, b) => b.totalScore - a.totalScore);

  return (
    <div className="min-h-screen bg-gradient-to-br from-yellow-900 to-purple-900 p-4">
      <div className="max-w-6xl mx-auto">
        
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">
            🏆 Scoring Phase
          </h1>
          <p className="text-yellow-200 text-lg">
            {gameOver 
              ? hasWinners 
                ? `Game Over! Winner${winners.length > 1 ? 's' : ''}: ${winners.join(', ')}`
                : "Game Complete"
              : "Round complete - Calculating scores"
            }
          </p>
          
          {redealMultiplier > 1 && (
            <div className="mt-2 inline-block bg-orange-500/20 border border-orange-500/30 rounded-lg px-3 py-1">
              <span className="text-orange-200 text-sm font-medium">
                Redeal Multiplier: {redealMultiplier}x Applied
              </span>
            </div>
          )}
        </div>

        {/* Score Breakdown */}
        <div className="mb-8">
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6">
            <h2 className="text-xl font-semibold text-white mb-6 text-center">
              Score Breakdown
            </h2>
            
            <div className="space-y-4">
              {sortedPlayers.map((player, index) => (
                <div 
                  key={player.name}
                  className={`
                    border rounded-xl p-4 transition-all
                    ${player.isWinner 
                      ? 'bg-gold-500/20 border-gold-400 ring-2 ring-gold-400' 
                      : 'bg-gray-700/50 border-gray-600'
                    }
                  `}
                >
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className={`
                        w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold
                        ${index === 0 ? 'bg-yellow-500 text-black' : 
                          index === 1 ? 'bg-gray-400 text-black' :
                          index === 2 ? 'bg-orange-600 text-white' :
                          'bg-gray-600 text-white'
                        }
                      `}>
                        {index + 1}
                      </div>
                      <PlayerSlot 
                        player={player} 
                        isActive={player.isWinner}
                        className="flex-shrink-0"
                      />
                      {player.isWinner && (
                        <span className="text-yellow-400 text-lg">👑</span>
                      )}
                    </div>
                    
                    <div className="text-right">
                      <div className="text-2xl font-bold text-white">
                        {player.totalScore}
                      </div>
                      <div className="text-sm text-gray-300">
                        Total Points
                      </div>
                    </div>
                  </div>
                  
                  {/* Round Score Details */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
                    <div className="bg-blue-500/20 border border-blue-500/30 rounded-lg p-3">
                      <div className="text-blue-300 mb-1">Declared</div>
                      <div className="text-white font-medium text-lg">
                        {player.pile_count !== undefined ? player.pile_count : '?'}
                      </div>
                    </div>
                    
                    <div className="bg-green-500/20 border border-green-500/30 rounded-lg p-3">
                      <div className="text-green-300 mb-1">Actual</div>
                      <div className="text-white font-medium text-lg">
                        {player.actualPiles !== undefined ? player.actualPiles : '?'} 
                      </div>
                    </div>
                    
                    <div className="bg-purple-500/20 border border-purple-500/30 rounded-lg p-3">
                      <div className="text-purple-300 mb-1">Base Score</div>
                      <div className="text-white font-medium text-lg">
                        {player.baseScore !== undefined ? player.baseScore : 0}
                      </div>
                    </div>
                    
                    <div className={`
                      border rounded-lg p-3
                      ${player.roundScore >= 0 
                        ? 'bg-green-500/20 border-green-500/30' 
                        : 'bg-red-500/20 border-red-500/30'
                      }
                    `}>
                      <div className={`mb-1 ${player.roundScore >= 0 ? 'text-green-300' : 'text-red-300'}`}>
                        Round Score
                      </div>
                      <div className={`font-bold text-lg ${player.roundScore >= 0 ? 'text-green-200' : 'text-red-200'}`}>
                        {player.roundScore >= 0 ? '+' : ''}{player.roundScore}
                      </div>
                    </div>
                  </div>
                  
                  {/* Score Explanation */}
                  <div className="mt-3 text-xs text-gray-400">
                    {player.scoreExplanation || 'Score calculation applied'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Scoring Rules Reference */}
        <div className="mb-8">
          <div className="bg-gray-800/50 border border-gray-600 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4 text-center">
              Scoring Rules
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div className="space-y-2">
                <div className="flex justify-between items-center p-2 bg-green-500/10 rounded">
                  <span className="text-gray-300">Declared 0, Got 0:</span>
                  <span className="text-green-400 font-medium">+3 Bonus</span>
                </div>
                <div className="flex justify-between items-center p-2 bg-green-500/10 rounded">
                  <span className="text-gray-300">Perfect Match:</span>
                  <span className="text-green-400 font-medium">Declared + 5</span>
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between items-center p-2 bg-red-500/10 rounded">
                  <span className="text-gray-300">Declared 0, Got &gt;0:</span>
                  <span className="text-red-400 font-medium">-Actual Piles</span>
                </div>
                <div className="flex justify-between items-center p-2 bg-red-500/10 rounded">
                  <span className="text-gray-300">Missed Target:</span>
                  <span className="text-red-400 font-medium">-|Difference|</span>
                </div>
              </div>
            </div>
            
            {redealMultiplier > 1 && (
              <div className="mt-4 text-center text-orange-300 text-sm">
                ⚠️ All scores multiplied by {redealMultiplier}x due to redeal
              </div>
            )}
          </div>
        </div>

        {/* Game Status and Actions */}
        <div className="mb-8">
          <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-6 text-center">
            {gameOver ? (
              <div>
                <h3 className="text-2xl font-bold text-white mb-4">
                  🎉 Game Complete!
                </h3>
                
                {hasWinners && (
                  <div className="mb-6">
                    <div className="text-yellow-300 text-lg mb-2">
                      Champion{winners.length > 1 ? 's' : ''}:
                    </div>
                    <div className="text-white text-xl font-bold">
                      {winners.join(' & ')}
                    </div>
                    <div className="text-gray-300 text-sm mt-1">
                      Final Score: {Math.max(...playersWithScores.map(p => p.totalScore))} points
                    </div>
                  </div>
                )}
                
                {onEndGame && (
                  <Button
                    onClick={onEndGame}
                    variant="primary"
                    size="large"
                    className="px-8"
                    aria-label="End game and return to lobby"
                  >
                    🏠 Return to Lobby
                  </Button>
                )}
              </div>
            ) : (
              <div>
                <h3 className="text-lg font-semibold text-blue-200 mb-4">
                  Round Complete
                </h3>
                
                <div className="mb-6 text-blue-100">
                  <div className="mb-2">
                    Highest Score: {Math.max(...sortedPlayers.map(p => p.totalScore))} points
                  </div>
                  <div className="text-sm text-gray-300">
                    Game ends at 50 points or after 20 rounds
                  </div>
                </div>
                
                {onStartNextRound && (
                  <Button
                    onClick={onStartNextRound}
                    variant="success"
                    size="large"
                    className="px-8"
                    aria-label="Start next round"
                  >
                    🎮 Start Next Round
                  </Button>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Status Footer */}
        <div className="text-center text-sm text-yellow-300">
          {gameOver ? (
            <div>Game completed with {sortedPlayers.length} players</div>
          ) : (
            <div>Round scoring complete - Ready for next round</div>
          )}
        </div>
      </div>
    </div>
  );
}

// No helper functions needed - all calculations done by backend

// PropTypes definition
ScoringUI.propTypes = {
  // Data props (all calculated by backend)
  players: PropTypes.arrayOf(PropTypes.shape({
    name: PropTypes.string.isRequired,
    pile_count: PropTypes.number,
    actualPiles: PropTypes.number
  })).isRequired,
  roundScores: PropTypes.objectOf(PropTypes.number),
  totalScores: PropTypes.objectOf(PropTypes.number),
  redealMultiplier: PropTypes.number,
  playersWithScores: PropTypes.arrayOf(PropTypes.shape({
    name: PropTypes.string.isRequired,
    pile_count: PropTypes.number,
    actualPiles: PropTypes.number,
    roundScore: PropTypes.number,
    totalScore: PropTypes.number,
    baseScore: PropTypes.number,
    scoreExplanation: PropTypes.string,
    isWinner: PropTypes.bool
  })),
  
  // State props
  gameOver: PropTypes.bool,
  winners: PropTypes.arrayOf(PropTypes.string),
  
  // Action props
  onStartNextRound: PropTypes.func,
  onEndGame: PropTypes.func
};

ScoringUI.defaultProps = {
  players: [],
  roundScores: {},
  totalScores: {},
  redealMultiplier: 1,
  playersWithScores: [],
  gameOver: false,
  winners: [],
  onStartNextRound: null,
  onEndGame: null
};

export default ScoringUI;