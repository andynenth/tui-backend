/**
 * 🎯 **DeclarationUI Component** - Pure Declaration Phase Interface
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

import React, { useState } from 'react';
import PropTypes from 'prop-types';
import GamePiece from "../GamePiece";
import PlayerSlot from "../PlayerSlot";
import Button from "../Button";

/**
 * Pure UI component for declaration phase
 */
export function DeclarationUI({
  // Data props
  myHand = [],
  declarations = {},
  players = [],
  currentTotal = 0,
  
  // State props (calculated by backend)
  isMyTurn = false,
  validOptions = [],
  declarationProgress = { declared: 0, total: 4 },
  isLastPlayer = false,
  estimatedPiles = 0,
  handStrength = 0,
  
  // Action props
  onDeclare
}) {
  // Debug props only once per component mount
  React.useEffect(() => {
    console.log('🎯 DECLARATION_UI_DEBUG: Props received:', {
      myHandLength: myHand?.length,
      declarations,
      playersLength: players?.length,
      currentTotal,
      isMyTurn,
      declarationProgress,
      isLastPlayer
    });
  }, []);
  const [selectedDeclaration, setSelectedDeclaration] = useState(null);
  const [showConfirmation, setShowConfirmation] = useState(false);
  
  const remainingDeclarations = declarationProgress.total - declarationProgress.declared;
  const isComplete = remainingDeclarations === 0;
  
  const handleDeclarationSelect = (value) => {
    setSelectedDeclaration(value);
    setShowConfirmation(true);
  };
  
  const handleConfirmDeclaration = () => {
    if (selectedDeclaration !== null && onDeclare) {
      onDeclare(selectedDeclaration);
      setSelectedDeclaration(null);
      setShowConfirmation(false);
    }
  };
  
  const handleCancelDeclaration = () => {
    setSelectedDeclaration(null);
    setShowConfirmation(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 to-blue-900 p-4">
      <div className="max-w-6xl mx-auto">
        
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">
            🎯 Declaration Phase
          </h1>
          <p className="text-purple-200 text-lg">
            {isComplete 
              ? "All declarations complete - Ready for Turn phase"
              : isMyTurn 
                ? "Your turn to declare target pile count"
                : "Waiting for other players to declare"
            }
          </p>
        </div>

        {/* Progress Indicator */}
        <div className="mb-8">
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-white">
                Declaration Progress
              </h2>
              <div className="text-purple-200 text-sm">
                {declarationProgress.declared} / {declarationProgress.total} complete
              </div>
            </div>
            
            <div className="w-full bg-gray-700 rounded-full h-3 mb-4">
              <div 
                className="bg-gradient-to-r from-purple-500 to-blue-500 h-3 rounded-full transition-all duration-500"
                style={{ width: `${(declarationProgress.declared / declarationProgress.total) * 100}%` }}
              />
            </div>
            
            <div className="text-center text-purple-200 text-sm">
              Current Total: <span className="font-bold text-white text-lg">{currentTotal}</span>
              {isLastPlayer && (
                <span className="ml-4 text-yellow-300">⚠️ Cannot total 8 (last player rule)</span>
              )}
            </div>
          </div>
        </div>

        {/* Players and Declarations */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-white mb-4 text-center">
            Player Declarations
          </h2>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {players.map((player) => {
              const playerDeclaration = declarations[player.name];
              const hasZeroStreak = player.zero_declares_in_a_row > 0;
              
              return (
                <div
                  key={player.name}
                  className={`
                    bg-white/10 backdrop-blur-md rounded-xl p-4 text-center
                    ${isMyTurn && player.name === players.find(p => !declarations[p.name])?.name 
                      ? 'ring-2 ring-blue-400 ring-offset-2 ring-offset-transparent' 
                      : ''
                    }
                  `}
                >
                  <PlayerSlot
                    player={player}
                    isActive={!isComplete && !declarations[player.name]}
                    className="mb-3"
                  />
                  
                  <div className="space-y-2">
                    {playerDeclaration !== undefined ? (
                      <div className="bg-green-500/20 border border-green-500/30 rounded-lg p-3">
                        <div className="text-green-300 text-sm mb-1">Declared</div>
                        <div className="text-white text-2xl font-bold">{playerDeclaration}</div>
                        <div className="text-green-200 text-xs">piles</div>
                      </div>
                    ) : (
                      <div className="bg-gray-500/20 border border-gray-500/30 rounded-lg p-3">
                        <div className="text-gray-400 text-sm">Waiting...</div>
                        <div className="text-gray-500 text-2xl">?</div>
                      </div>
                    )}
                    
                    {hasZeroStreak && (
                      <div className="bg-yellow-500/20 border border-yellow-500/30 rounded-lg p-2">
                        <div className="text-yellow-300 text-xs">
                          ⚠️ {player.zero_declares_in_a_row} zero streak{player.zero_declares_in_a_row > 1 ? 's' : ''}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* My Hand */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-white mb-4 text-center">
            My Hand
          </h2>
          
          {myHand.length > 0 ? (
            <div className="flex flex-wrap justify-center gap-2">
              {myHand.map((card, index) => (
                <GamePiece
                  key={`${card.color}-${card.point}-${index}`}
                  piece={card}
                  size="md"
                  className="transform hover:scale-105 transition-transform"
                />
              ))}
            </div>
          ) : (
            <div className="text-center text-gray-400 py-8">
              <div className="text-4xl mb-2">🃏</div>
              <p>No cards in hand</p>
            </div>
          )}
          
          {/* Hand Analysis */}
          {myHand.length > 0 && (
            <div className="mt-4 text-center text-sm text-purple-200">
              <div>Total Cards: {myHand.length}</div>
              <div>Estimated Piles: {estimatedPiles}</div>
              <div>Hand Strength: {handStrength}</div>
            </div>
          )}
        </div>

        {/* Declaration Interface */}
        {isMyTurn && !isComplete && (
          <div className="mb-8">
            <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-blue-200 mb-4 text-center">
                Make Your Declaration
              </h3>
              
              {!showConfirmation ? (
                <div>
                  <p className="text-blue-100 mb-6 text-center">
                    Choose how many piles you think you&apos;ll win this round:
                  </p>
                  
                  <div className="grid grid-cols-3 lg:grid-cols-9 gap-3 mb-6">
                    {[0, 1, 2, 3, 4, 5, 6, 7, 8].map((value) => {
                      const isValid = validOptions.includes(value);
                      const wouldTotal8 = isLastPlayer && (currentTotal + value === 8);
                      
                      return (
                        <button
                          key={value}
                          onClick={() => isValid && !wouldTotal8 && handleDeclarationSelect(value)}
                          disabled={!isValid || wouldTotal8}
                          className={`
                            aspect-square rounded-xl text-2xl font-bold border-2 transition-all
                            ${isValid && !wouldTotal8
                              ? 'bg-blue-500/20 border-blue-400 text-white hover:bg-blue-500/40 hover:scale-105'
                              : 'bg-gray-500/20 border-gray-600 text-gray-500 cursor-not-allowed'
                            }
                            ${wouldTotal8 ? 'bg-red-500/20 border-red-400 text-red-300' : ''}
                          `}
                          aria-label={`Declare ${value} piles${wouldTotal8 ? ' (forbidden - would total 8)' : ''}`}
                        >
                          {value}
                          {wouldTotal8 && <div className="text-xs">❌</div>}
                        </button>
                      );
                    })}
                  </div>
                  
                  <div className="text-sm text-blue-200 text-center space-y-1">
                    <div>Valid options: {validOptions.join(', ')}</div>
                    {isLastPlayer && (
                      <div className="text-yellow-300">
                        ⚠️ As the last player, you cannot make the total equal 8
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="text-center">
                  <p className="text-blue-100 mb-6">
                    Confirm your declaration of <span className="font-bold text-white text-xl">{selectedDeclaration}</span> piles?
                  </p>
                  
                  <div className="flex justify-center gap-4">
                    <Button
                      onClick={handleConfirmDeclaration}
                      variant="success"
                      size="large"
                      className="px-8"
                      aria-label="Confirm declaration"
                    >
                      ✅ Confirm
                    </Button>
                    
                    <Button
                      onClick={handleCancelDeclaration}
                      variant="secondary"
                      size="large"
                      className="px-8"
                      aria-label="Cancel declaration"
                    >
                      ❌ Cancel
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Waiting State */}
        {!isMyTurn && !isComplete && (
          <div className="mb-8">
            <div className="bg-gray-500/10 border border-gray-500/20 rounded-xl p-6 text-center">
              <div className="text-gray-300 mb-4">
                Waiting for other players to declare...
              </div>
              <div className="flex justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-400"></div>
              </div>
            </div>
          </div>
        )}

        {/* Status Footer */}
        <div className="text-center text-sm text-purple-300">
          {isComplete ? (
            <div>✅ All declarations complete - Moving to Turn phase</div>
          ) : (
            <div>⏳ {remainingDeclarations} player{remainingDeclarations !== 1 ? 's' : ''} remaining</div>
          )}
        </div>
      </div>
    </div>
  );
}

// No helper functions needed - all calculations done by backend

// PropTypes definition
DeclarationUI.propTypes = {
  // Data props
  myHand: PropTypes.arrayOf(PropTypes.shape({
    color: PropTypes.string.isRequired,
    point: PropTypes.number.isRequired,
    kind: PropTypes.string.isRequired
  })),
  declarations: PropTypes.objectOf(PropTypes.number),
  players: PropTypes.arrayOf(PropTypes.shape({
    name: PropTypes.string.isRequired,
    zero_declares_in_a_row: PropTypes.number
  })).isRequired,
  currentTotal: PropTypes.number,
  
  // State props (calculated by backend)
  isMyTurn: PropTypes.bool,
  validOptions: PropTypes.arrayOf(PropTypes.number),
  declarationProgress: PropTypes.shape({
    declared: PropTypes.number.isRequired,
    total: PropTypes.number.isRequired
  }),
  isLastPlayer: PropTypes.bool,
  estimatedPiles: PropTypes.number,
  handStrength: PropTypes.number,
  
  // Action props
  onDeclare: PropTypes.func
};

DeclarationUI.defaultProps = {
  myHand: [],
  declarations: {},
  currentTotal: 0,
  isMyTurn: false,
  validOptions: [],
  declarationProgress: { declared: 0, total: 4 },
  isLastPlayer: false,
  estimatedPiles: 0,
  handStrength: 0,
  onDeclare: () => {}
};

export default DeclarationUI;