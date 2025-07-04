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
import PlayerSlot from "../PlayerSlot";
import Button from "../Button";

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
  onStartNextRound
}) {
  // Debug logging
  console.log('🏆 SCORING_UI_DEBUG: ScoringUI props received:');
  console.log('  👥 players:', players);
  console.log('  📊 roundScores:', roundScores);
  console.log('  💯 totalScores:', totalScores);
  console.log('  ⚗️ redealMultiplier:', redealMultiplier);
  console.log('  🧮 playersWithScores:', playersWithScores);
  console.log('  🏁 gameOver:', gameOver);
  console.log('  🏆 winners:', winners);
  const hasWinners = winners.length > 0;
  // Use backend-provided sorted players, or fallback to manual sort if needed
  const sortedPlayers = playersWithScores.length > 0 ? playersWithScores : 
    players.map(player => {
      const playerData = {
        ...player,
        roundScore: roundScores[player.name] || 0,
        totalScore: totalScores[player.name] || 0,
        isWinner: winners.includes(player.name)
      };
      console.log(`🔍 SCORING_UI_DEBUG: Mapped player ${player.name}:`, playerData);
      return playerData;
    }).sort((a, b) => b.totalScore - a.totalScore);
  
  console.log('🎯 SCORING_UI_DEBUG: Final sortedPlayers:', sortedPlayers);

  return (
    <div className="min-h-screen bg-gradient-to-br from-yellow-900 to-purple-900 p-3">
      <div className="max-w-7xl mx-auto">
        
        {/* Compact Header */}
        <div className="text-center mb-4">
          <h1 className="text-3xl font-bold text-white mb-1">🏆 Round Results</h1>
          <p className="text-yellow-200">
            {gameOver 
              ? hasWinners 
                ? `Game Over! Winner${winners.length > 1 ? 's' : ''}: ${winners.join(', ')}`
                : "Game Complete"
              : "Round complete"
            }
            {redealMultiplier > 1 && (
              <span className="ml-2 text-orange-300">({redealMultiplier}x multiplier)</span>
            )}
          </p>
        </div>

        {/* Main Content Grid - Side by Side */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
          
          {/* Left Column: Player Scores (Compact) */}
          <div className="lg:col-span-2">
            <div className="bg-white/10 backdrop-blur-md rounded-xl p-4">
              <h2 className="text-lg font-semibold text-white mb-4 text-center">Player Scores</h2>
              
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
                {sortedPlayers.map((player, index) => (
                  <div 
                    key={player.name}
                    className={`
                      border rounded-lg p-3 transition-all
                      ${player.isWinner 
                        ? 'bg-gold-500/20 border-gold-400 ring-1 ring-gold-400' 
                        : 'bg-gray-700/50 border-gray-600'
                      }
                    `}
                  >
                    {/* Player Header Row */}
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <div className={`
                          w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold
                          ${index === 0 ? 'bg-yellow-500 text-black' : 
                            index === 1 ? 'bg-gray-400 text-black' :
                            index === 2 ? 'bg-orange-600 text-white' :
                            'bg-gray-600 text-white'
                          }
                        `}>
                          {index + 1}
                        </div>
                        <PlayerSlot occupant={player} isActive={player.isWinner} className="flex-shrink-0" />
                        {player.isWinner && <span className="text-yellow-400">👑</span>}
                      </div>
                      <div className="text-right">
                        <div className="text-xl font-bold text-white">{player.totalScore}</div>
                        <div className="text-xs text-gray-300">Total</div>
                      </div>
                    </div>
                    
                    {/* Compact Score Grid */}
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="bg-blue-500/20 border border-blue-500/30 rounded p-2 text-center">
                        <div className="text-blue-300">Declared</div>
                        <div className="text-white font-medium text-sm">
                          {player.pile_count !== undefined ? player.pile_count : '?'}
                        </div>
                      </div>
                      
                      <div className="bg-green-500/20 border border-green-500/30 rounded p-2 text-center">
                        <div className="text-green-300">Actual</div>
                        <div className="text-white font-medium text-sm">
                          {player.actualPiles !== undefined ? player.actualPiles : '?'}
                        </div>
                      </div>
                      
                      <div className="bg-purple-500/20 border border-purple-500/30 rounded p-2 text-center">
                        <div className="text-purple-300">Base</div>
                        <div className="text-white font-medium text-sm">
                          {player.baseScore !== undefined ? player.baseScore : '?'}
                        </div>
                      </div>
                      
                      <div className={`
                        border rounded p-2 text-center
                        ${player.roundScore >= 0 
                          ? 'bg-green-500/20 border-green-500/30' 
                          : 'bg-red-500/20 border-red-500/30'
                        }
                      `}>
                        <div className={`${player.roundScore >= 0 ? 'text-green-300' : 'text-red-300'}`}>
                          Round
                        </div>
                        <div className={`font-bold text-sm ${player.roundScore >= 0 ? 'text-green-200' : 'text-red-200'}`}>
                          {player.roundScore >= 0 ? '+' : ''}{player.roundScore}
                        </div>
                      </div>
                    </div>
                    
                    {/* Score Explanation */}
                    <div className="mt-2 text-xs text-gray-400 text-center">
                      {player.scoreExplanation || 'Score calculated'}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right Column: Rules & Actions */}
          <div className="space-y-4">
            
            {/* Scoring Rules Reference (Compact) */}
            <div className="bg-gray-800/50 border border-gray-600 rounded-xl p-4">
              <h3 className="text-base font-semibold text-white mb-3 text-center">Scoring Rules</h3>
              
              <div className="space-y-2 text-xs">
                <div className="flex justify-between items-center p-2 bg-green-500/10 rounded">
                  <span className="text-gray-300">Perfect Zero:</span>
                  <span className="text-green-400 font-medium">+3</span>
                </div>
                <div className="flex justify-between items-center p-2 bg-green-500/10 rounded">
                  <span className="text-gray-300">Perfect Match:</span>
                  <span className="text-green-400 font-medium">Declared + 5</span>
                </div>
                <div className="flex justify-between items-center p-2 bg-red-500/10 rounded">
                  <span className="text-gray-300">Broke Zero:</span>
                  <span className="text-red-400 font-medium">-Actual</span>
                </div>
                <div className="flex justify-between items-center p-2 bg-red-500/10 rounded">
                  <span className="text-gray-300">Missed Target:</span>
                  <span className="text-red-400 font-medium">-|Difference|</span>
                </div>
              </div>
              
              {redealMultiplier > 1 && (
                <div className="mt-3 text-center text-orange-300 text-xs p-2 bg-orange-500/10 rounded">
                  ⚠️ All scores ×{redealMultiplier} (redeal penalty)
                </div>
              )}
            </div>

            {/* Game Status and Actions */}
            <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-4 text-center">
              <div>
                <h3 className="text-lg font-semibold text-blue-200 mb-3">Round Complete</h3>
                
                <div className="mb-4 text-blue-100">
                  <div className="mb-1">Highest Score: {Math.max(...sortedPlayers.map(p => p.totalScore))} points</div>
                  <div className="text-sm text-gray-300">Game ends at 50 points or after 20 rounds</div>
                </div>
                
                {!gameOver && onStartNextRound && (
                  <Button
                    onClick={onStartNextRound}
                    variant="success"
                    size="large"
                    className="px-6"
                      aria-label="Start next round"
                    >
                      🎮 Start Next Round
                    </Button>
                  )}
              </div>
            </div>

          </div>
        </div>

        {/* Compact Status Footer */}
        <div className="text-center text-sm text-yellow-300">
          <div>✅ Round scoring complete{gameOver ? ' - Final round' : ' - Ready for next round'}</div>
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
  onStartNextRound: PropTypes.func
};

ScoringUI.defaultProps = {
  players: [],
  roundScores: {},
  totalScores: {},
  redealMultiplier: 1,
  playersWithScores: [],
  gameOver: false,
  winners: [],
  onStartNextRound: null
};

export default ScoringUI;