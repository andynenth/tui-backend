/**
 * 🏆 **TurnResultsUI Component** - Pure Turn Completion Results Interface
 * 
 * Features:
 * ✅ Pure functional component (props in, JSX out)
 * ✅ Display timing controls with auto-advance and skip functionality
 * ✅ Comprehensive prop interfaces
 * ✅ Accessible and semantic HTML
 * ✅ Tailwind CSS styling
 * 🚀 EVENT-DRIVEN: Frontend display timing control
 */

import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import GamePiece from "../GamePiece";
import PlayerSlot from "../PlayerSlot";
import Button from "../Button";

/**
 * UI component for turn completion results with display timing control
 */
export function TurnResultsUI({
  // Data props
  winner = null,
  winningPlay = null,
  playerPiles = {},
  players = [],
  turnNumber = 1,
  nextStarter = null,
  
  // 🚀 EVENT-DRIVEN: Display timing props
  displayMetadata = null,
  onAutoAdvance = null,
  onSkip = null
}) {
  // 🚀 EVENT-DRIVEN: Display timing state
  const [timeRemaining, setTimeRemaining] = useState(null);
  const [isSkipped, setIsSkipped] = useState(false);
  
  // Extract display configuration from metadata
  // Phase 5.2: Reduce auto-advance timer for <50ms state sync optimization
  const showForSeconds = displayMetadata?.show_for_seconds || 3.0; // Reduced from 7.0s to 3.0s
  const autoAdvance = displayMetadata?.auto_advance !== false;
  const canSkip = displayMetadata?.can_skip !== false;
  // 🚀 EVENT-DRIVEN: Auto-advance timer
  useEffect(() => {
    if (!autoAdvance || isSkipped) return;
    
    // Initialize countdown
    setTimeRemaining(showForSeconds);
    
    const timer = setInterval(() => {
      setTimeRemaining(prev => {
        if (prev <= 1) {
          clearInterval(timer);
          console.log('🚀 AUTO_ADVANCE: Timer expired, triggering auto-advance');
          if (onAutoAdvance) onAutoAdvance();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    
    return () => clearInterval(timer);
  }, [autoAdvance, showForSeconds, isSkipped, onAutoAdvance]);
  
  // Handle skip button
  const handleSkip = () => {
    console.log('🚀 SKIP: User requested skip');
    setIsSkipped(true);
    setTimeRemaining(0);
    if (onSkip) onSkip();
  };
  
  // Debug logging for turn results
  console.log('🏆 TURN_RESULTS_UI_DEBUG: TurnResultsUI component rendered with props:');
  console.log('  🏅 winner:', winner);
  console.log('  🎯 winningPlay:', winningPlay);
  console.log('  📊 playerPiles:', playerPiles);
  console.log('  👥 players:', players);
  console.log('  🔢 turnNumber:', turnNumber);
  console.log('  🎪 nextStarter:', nextStarter);
  console.log('  🚀 displayMetadata:', displayMetadata);
  console.log('  ⏰ timeRemaining:', timeRemaining);
  
  const hasWinner = !!winner;
  const winningPieces = winningPlay?.pieces || [];
  const winningValue = winningPlay?.value || 0;
  const winningType = winningPlay?.type || 'unknown';
  const pilesWon = winningPlay?.pilesWon || 0;
  
  console.log('🏆 TURN_RESULTS_UI_DEBUG: Computed values:');
  console.log('  ✅ hasWinner:', hasWinner);
  console.log('  🃏 winningPieces:', winningPieces);
  console.log('  💎 winningValue:', winningValue);
  console.log('  🎲 winningType:', winningType);
  console.log('  🏆 pilesWon:', pilesWon);

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-900 to-emerald-900 p-4">
      <div className="max-w-6xl mx-auto">
        
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">
            🏆 Turn {turnNumber} Results
          </h1>
          <p className="text-green-200 text-lg">
            {hasWinner 
              ? `${winner} wins the turn!`
              : "Turn completed - no winner"
            }
          </p>
        </div>

        {/* Winner Display */}
        {hasWinner && (
          <div className="mb-8">
            <div className="bg-yellow-500/20 border border-yellow-500/30 rounded-xl p-6">
              <div className="text-center mb-6">
                <div className="text-6xl mb-4">👑</div>
                <h2 className="text-2xl font-bold text-yellow-200 mb-2">
                  Turn Winner: {winner}
                </h2>
                <p className="text-yellow-100">
                  Wins {pilesWon} pile{pilesWon !== 1 ? 's' : ''} with {winningType}
                </p>
              </div>
              
              {/* Winning Play */}
              {winningPieces.length > 0 && (
                <div className="bg-gray-800/50 rounded-lg p-4">
                  <h3 className="text-white font-medium mb-3 text-center">
                    Winning Play:
                  </h3>
                  <div className="flex flex-wrap justify-center gap-2 mb-3">
                    {winningPieces.map((piece, index) => (
                      <GamePiece
                        key={`winning-${index}`}
                        piece={piece}
                        size="medium"
                        className="ring-2 ring-yellow-400 ring-offset-2 ring-offset-gray-800"
                      />
                    ))}
                  </div>
                  <div className="text-center text-gray-300">
                    <div>Type: <span className="text-yellow-300">{winningType}</span></div>
                    <div>Value: <span className="text-yellow-300">{winningValue}</span></div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Current Pile Scores */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-white mb-4 text-center">
            Current Pile Scores
          </h2>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {players.map((player) => {
              const playerName = typeof player === 'string' ? player : player.name;
              const pileCount = playerPiles[playerName] || 0;
              const isWinner = playerName === winner;
              const isNextStarter = playerName === nextStarter;
              
              return (
                <div
                  key={playerName}
                  className={`
                    bg-white/10 backdrop-blur-md rounded-xl p-4 text-center transition-all
                    ${isWinner ? 'ring-2 ring-yellow-400 ring-offset-2 ring-offset-transparent scale-105' : ''}
                    ${isNextStarter ? 'bg-blue-500/20 border border-blue-400/50' : ''}
                  `}
                >
                  <PlayerSlot
                    occupant={player}
                    isActive={isNextStarter}
                    className="mb-3"
                  />
                  
                  <div className="space-y-2">
                    <div className={`
                      rounded-lg p-3 border
                      ${isWinner 
                        ? 'bg-yellow-500/20 border-yellow-500/30' 
                        : 'bg-gray-500/20 border-gray-500/30'
                      }
                    `}>
                      <div className={`text-sm mb-1 ${isWinner ? 'text-yellow-300' : 'text-gray-300'}`}>
                        Piles
                      </div>
                      <div className={`text-2xl font-bold ${isWinner ? 'text-yellow-200' : 'text-white'}`}>
                        {pileCount}
                      </div>
                    </div>
                    
                    {isWinner && (
                      <div className="bg-yellow-500/20 border border-yellow-500/30 rounded-lg p-2">
                        <div className="text-yellow-300 text-xs">
                          🏆 +{pilesWon} this turn
                        </div>
                      </div>
                    )}
                    
                    {isNextStarter && (
                      <div className="bg-blue-500/20 border border-blue-500/30 rounded-lg p-2">
                        <div className="text-blue-300 text-xs">
                          🎯 Next starter
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Summary Stats */}
        <div className="mb-8">
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4 text-center">
              Turn Summary
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
              <div className="space-y-2">
                <div className="text-gray-300 text-sm">Turn Number</div>
                <div className="text-white text-xl font-bold">{turnNumber}</div>
              </div>
              <div className="space-y-2">
                <div className="text-gray-300 text-sm">Winner</div>
                <div className="text-white text-xl font-bold">
                  {hasWinner ? winner : "No winner"}
                </div>
              </div>
              <div className="space-y-2">
                <div className="text-gray-300 text-sm">Piles Awarded</div>
                <div className="text-white text-xl font-bold">{pilesWon}</div>
              </div>
            </div>
          </div>
        </div>

        {/* Next Turn Info */}
        {nextStarter && (
          <div className="mb-8">
            <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-6 text-center">
              <h3 className="text-lg font-semibold text-blue-200 mb-2">
                Next Turn
              </h3>
              <p className="text-blue-100 mb-4">
                {nextStarter === winner 
                  ? `${nextStarter} wins and starts the next turn`
                  : `${nextStarter} will start the next turn`
                }
              </p>
              <div className="text-sm text-blue-200">
                Turn order will be updated accordingly
              </div>
            </div>
          </div>
        )}

        {/* 🚀 EVENT-DRIVEN: Display Timing Controls */}
        <div className="text-center">
          <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-6">
            {autoAdvance && timeRemaining > 0 && !isSkipped ? (
              <>
                <div className="text-blue-200 text-lg font-medium mb-2">
                  🔄 Auto-continuing to next turn...
                </div>
                <div className="text-blue-300 text-sm mb-4">
                  Next turn starts in <span className="font-bold text-blue-200">{timeRemaining}</span> seconds
                </div>
                {canSkip && (
                  <Button
                    onClick={handleSkip}
                    variant="secondary"
                    className="bg-blue-600 hover:bg-blue-700 text-white"
                  >
                    Skip Wait ⏭️
                  </Button>
                )}
              </>
            ) : (
              <>
                <div className="text-blue-200 text-lg font-medium mb-2">
                  {isSkipped ? '⏭️ Skipped' : '✅ Ready to continue'}
                </div>
                <div className="text-blue-300 text-sm">
                  Next turn will start automatically
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// PropTypes definition
TurnResultsUI.propTypes = {
  // Data props
  winner: PropTypes.string,
  winningPlay: PropTypes.shape({
    pieces: PropTypes.arrayOf(PropTypes.shape({
      suit: PropTypes.string,
      value: PropTypes.oneOfType([PropTypes.string, PropTypes.number])
    })),
    value: PropTypes.number,
    type: PropTypes.string,
    pilesWon: PropTypes.number
  }),
  playerPiles: PropTypes.objectOf(PropTypes.number),
  players: PropTypes.arrayOf(PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.shape({
      name: PropTypes.string.isRequired
    })
  ])).isRequired,
  turnNumber: PropTypes.number,
  nextStarter: PropTypes.string,
  
  // 🚀 EVENT-DRIVEN: Display timing props
  displayMetadata: PropTypes.shape({
    type: PropTypes.string,
    show_for_seconds: PropTypes.number,
    auto_advance: PropTypes.bool,
    can_skip: PropTypes.bool,
    next_phase: PropTypes.string
  }),
  onAutoAdvance: PropTypes.func,
  onSkip: PropTypes.func
};

TurnResultsUI.defaultProps = {
  winner: null,
  winningPlay: null,
  playerPiles: {},
  turnNumber: 1,
  nextStarter: null,
  
  // 🚀 EVENT-DRIVEN: Display timing defaults
  displayMetadata: null,
  onAutoAdvance: null,
  onSkip: null
};

export default TurnResultsUI;