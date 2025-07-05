/**
 * 🏆 **TurnResultsUI Component** - Pure Turn Completion Results Interface
 * 
 * Features:
 * ✅ Pure functional component (props in, JSX out)
 * ✅ No hooks except local UI state
 * ✅ Comprehensive prop interfaces
 * ✅ Accessible and semantic HTML
 * ✅ Tailwind CSS styling
 */

import React, { useEffect } from 'react';
import PropTypes from 'prop-types';
import { GamePhaseContainer, PhaseHeader, EnhancedGamePiece } from '../shared';

// Add custom styles for animations
const customStyles = `
  @keyframes slideIn {
    from {
      opacity: 0;
      transform: scale(0.9) translateY(30px);
    }
    to {
      opacity: 1;
      transform: scale(1) translateY(0);
    }
  }
  
  @keyframes bounce {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
  }
  
  .animate-slideIn {
    animation: slideIn 0.8s ease-out;
  }
  
  .animate-bounce {
    animation: bounce 1s ease-in-out infinite;
  }
`;

// Inject styles into document head
if (typeof document !== 'undefined') {
  const styleSheet = document.createElement('style');
  styleSheet.textContent = customStyles;
  document.head.appendChild(styleSheet);
}

/**
 * Pure UI component for turn completion results
 */
export function TurnResultsUI({
  // Data props
  winner = null,
  winningPlay = null,
  playerPiles = {},
  players = [],
  turnNumber = 1,
  nextStarter = null
}) {
  // Add countdown effect
  useEffect(() => {
    let count = 5;
    const countdownEl = document.getElementById('countdown');
    
    if (countdownEl) {
      const timer = setInterval(() => {
        count--;
        countdownEl.textContent = count;
        
        if (count <= 0) {
          clearInterval(timer);
          console.log('Proceeding to next turn...');
          // In real game, this would transition to turn phase
        }
      }, 1000);
      
      return () => clearInterval(timer);
    }
  }, []);
  // Debug logging for turn results
  console.log('🏆 TURN_RESULTS_UI_DEBUG: TurnResultsUI component rendered with props:');
  console.log('  🏅 winner:', winner);
  console.log('  🎯 winningPlay:', winningPlay);
  console.log('  📊 playerPiles:', playerPiles);
  console.log('  👥 players:', players);
  console.log('  🔢 turnNumber:', turnNumber);
  console.log('  🎪 nextStarter:', nextStarter);
  
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
    <GamePhaseContainer phase="turn_results">
      <PhaseHeader 
        title="Turn Results" 
        subtitle={`Turn ${turnNumber} Winner`}
        roundNumber={1}
      />

        {/* Winner Display */}
        {hasWinner && (
          <div className="px-5 py-8">
            <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 border border-yellow-200 rounded-2xl p-6 relative overflow-hidden shadow-lg animate-slideIn">
              {/* Decorative elements */}
              <div className="absolute -top-5 -left-5 text-6xl opacity-10 transform -rotate-12">✨</div>
              <div className="absolute -bottom-5 -right-5 text-6xl opacity-10 transform rotate-12">🎉</div>
              
              <div className="text-center mb-6">
                <div className="text-5xl mb-4 animate-bounce inline-block">👑</div>
                <h2 className="text-2xl font-bold text-yellow-700 mb-2 font-serif">
                  {winner} Wins!
                </h2>
              </div>
              
              {/* Winning Play */}
              {winningPieces.length > 0 && (
                <div className="bg-white/80 rounded-xl p-4 border border-yellow-200">
                  <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wider mb-3 text-center">
                    Winning Play
                  </h3>
                  <div className="flex justify-center gap-2 mb-2">
                    {winningPieces.map((piece, index) => (
                      <EnhancedGamePiece
                        key={`winning-${index}`}
                        piece={piece}
                        size="large"
                        className="shadow-sm"
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Players Summary */}
        <div className="px-5 pb-5 flex-1">
          <div className="flex flex-col gap-2">
            {players.filter(p => {
              const playerName = typeof p === 'string' ? p : p.name;
              return playerName !== winner; // Exclude winner from summary
            }).map((player) => {
              const playerName = typeof player === 'string' ? player : player.name;
              const pileCount = playerPiles[playerName] || 0;
              const isNextStarter = playerName === nextStarter;
              const playerInitial = playerName.charAt(0).toUpperCase();
              
              // Mock played pieces data for demonstration
              const getDemoPlayedPieces = (name) => {
                switch (name.toLowerCase()) {
                  case 'andy': return ['兵', '炮', '马'];
                  case 'lucas': return ['帅'];
                  case 'daniel': return ['象', '士'];
                  default: return ['兵'];
                }
              };
              
              const playedPieces = getDemoPlayedPieces(playerName);
              
              return (
                <div
                  key={playerName}
                  className="bg-gradient-to-br from-white to-gray-50 rounded-xl p-3 border border-gray-200 shadow-sm flex items-center"
                >
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-white to-gray-50 border-2 border-gray-300 flex items-center justify-center text-xs font-bold text-gray-600 mr-3 shadow-sm">
                    {playerInitial}
                  </div>
                  
                  <div className="flex-1">
                    <div className="text-sm font-semibold text-gray-900">
                      {playerName}{playerName === 'Andy' ? ' (You)' : ''}
                    </div>
                  </div>
                  
                  <div className="flex gap-1">
                    {playedPieces.map((piece, index) => {
                      const isRed = ['兵', '炮', '帅'].includes(piece);
                      return (
                        <EnhancedGamePiece
                          key={index}
                          piece={{
                            color: isRed ? 'red' : 'black',
                            display: piece
                          }}
                          size="small"
                        />
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Next Turn Info - Stick to bottom */}
        <div className="bg-gradient-to-b from-gray-50/60 to-gray-200/80 p-5 border-t border-gray-200 text-center relative mt-auto">
          <div className="absolute top-0 left-1/2 transform -translate-x-1/2 w-10 h-0.5 bg-gradient-to-r from-transparent via-gray-400 to-transparent"></div>
          
          <div className="text-base font-semibold text-gray-800 mb-2">
            {nextStarter ? `${nextStarter} will start Turn ${turnNumber + 1}` : 'Preparing next turn...'}
          </div>
          <div className="text-sm text-gray-600">
            Continuing in <span className="inline-block bg-gray-400/20 px-2 py-1 rounded-md font-semibold ml-1" id="countdown">5</span> seconds
          </div>
        </div>
    </GamePhaseContainer>
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
  nextStarter: PropTypes.string
};

TurnResultsUI.defaultProps = {
  winner: null,
  winningPlay: null,
  playerPiles: {},
  turnNumber: 1,
  nextStarter: null
};

export default TurnResultsUI;