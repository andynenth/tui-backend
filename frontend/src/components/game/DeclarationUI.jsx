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
import Button from "../Button";
import { GamePhaseContainer, PhaseHeader, HandSection } from '../shared';

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
    console.log('🎯 DECLARATION_UI_DEBUG: Full players array:', players);
    console.log('🎯 DECLARATION_UI_DEBUG: Full declarations object:', declarations);
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
    <GamePhaseContainer phase="declaration">
      <PhaseHeader 
        title="Declaration" 
        subtitle="Target Pile Counts"
        roundNumber={1}
      />

      {/* Player Declaration Grid */}
      <div className="px-5 py-4 flex-1">
        <div className="grid grid-cols-2 gap-3 mb-6">
          {players.map((player) => {
            const playerDeclaration = declarations[player.name];
            const isCurrentPlayer = isMyTurn && player.name === 'Andy'; // Assuming Andy is the current user
            const hasDeclaration = playerDeclaration !== undefined;
            const playerInitial = player.name.charAt(0).toUpperCase();
            
            return (
              <div
                key={player.name}
                className={`
                  bg-gradient-to-br from-white to-gray-50 rounded-xl p-4 border border-gray-200 shadow-sm
                  ${isCurrentPlayer ? 'ring-2 ring-blue-400 ring-offset-1' : ''}
                `}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-white to-gray-50 border-2 border-gray-300 flex items-center justify-center text-xs font-bold text-gray-600 mr-3 shadow-sm">
                      {playerInitial}
                    </div>
                    <div className="text-sm font-semibold text-gray-900">
                      {player.name}{player.name === 'Andy' ? ' (You)' : ''}
                    </div>
                  </div>
                  
                  <div className="text-right">
                    {hasDeclaration ? (
                      <div className="text-lg font-bold text-blue-600">
                        {playerDeclaration}
                      </div>
                    ) : (
                      <div className="text-sm text-gray-500">
                        {isCurrentPlayer ? 'Your turn' : 'Waiting...'}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
        
        {/* Declaration Total */}
        <div className="text-center mb-6">
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
            <div className="text-sm text-blue-600 mb-1">Current Total</div>
            <div className="text-2xl font-bold text-blue-700">{currentTotal}</div>
            {isLastPlayer && (
              <div className="text-xs text-orange-600 mt-1">⚠️ Cannot total 8</div>
            )}
          </div>
        </div>
      </div>

      {/* Declaration Modal */}
      {isMyTurn && !showConfirmation && (
        <div className="px-5 pb-4">
          <div className="bg-blue-50 border border-blue-200 rounded-2xl p-6">
            <h3 className="text-lg font-semibold text-blue-700 mb-4 text-center">
              Make Your Declaration
            </h3>
            
            <p className="text-blue-600 mb-4 text-center text-sm">
              Choose how many piles you think you'll win this round:
            </p>
            
            <div className="grid grid-cols-3 gap-3 mb-4">
              {[0, 1, 2, 3, 4, 5, 6, 7, 8].map((value) => {
                const isValid = validOptions.includes(value);
                const wouldTotal8 = isLastPlayer && (currentTotal + value === 8);
                
                return (
                  <button
                    key={value}
                    onClick={() => isValid && !wouldTotal8 && handleDeclarationSelect(value)}
                    disabled={!isValid || wouldTotal8}
                    className={`
                      aspect-square rounded-xl text-xl font-bold border-2 transition-all
                      ${isValid && !wouldTotal8
                        ? 'bg-blue-500 border-blue-600 text-white hover:bg-blue-600 hover:scale-105'
                        : 'bg-gray-200 border-gray-300 text-gray-400 cursor-not-allowed'
                      }
                      ${wouldTotal8 ? 'bg-red-100 border-red-300 text-red-500' : ''}
                    `}
                  >
                    {value}
                  </button>
                );
              })}
            </div>
            
            {isLastPlayer && (
              <div className="text-xs text-orange-600 text-center">
                ⚠️ Cannot make total equal 8
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* Confirmation Modal */}
      {showConfirmation && (
        <div className="px-5 pb-4">
          <div className="bg-green-50 border border-green-200 rounded-2xl p-6 text-center">
            <p className="text-green-700 mb-4">
              Confirm declaration of <span className="font-bold text-xl">{selectedDeclaration}</span> piles?
            </p>
            
            <div className="flex justify-center gap-3">
              <Button
                onClick={handleConfirmDeclaration}
                variant="success"
                size="medium"
                className="px-6"
              >
                ✅ Confirm
              </Button>
              
              <Button
                onClick={handleCancelDeclaration}
                variant="secondary"
                size="medium"
                className="px-6"
              >
                ❌ Cancel
              </Button>
            </div>
          </div>
        </div>
      )}
      
      {/* Hand Section */}
      <HandSection 
        pieces={myHand}
        isActivePlayer={isMyTurn}
        disabled={true}
      />
    </GamePhaseContainer>
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