/**
 * 🎮 **TurnUI Component** - Pure Turn Phase Interface
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
import Button from "../Button";

// Helper function to calculate piece value (same logic as GamePiece)
const calculatePieceValue = (piece) => {
  if (!piece) return 0;
  
  if (typeof piece === 'string') {
    const match = piece.match(/\((\d+)\)/);
    return match ? parseInt(match[1]) : 0;
  }
  
  return piece.point || piece.value || 0;
};

// Helper function to calculate total value of pieces array
const calculateTotalValue = (pieces) => {
  if (!Array.isArray(pieces)) return 0;
  return pieces.reduce((sum, piece) => sum + calculatePieceValue(piece), 0);
};

/**
 * Pure UI component for turn phase
 */
export function TurnUI({
  // Data props
  myHand = [],
  currentTurnPlays = [],
  requiredPieceCount = null,
  turnNumber = 1,
  
  // State props (calculated by backend)
  isMyTurn = false,
  canPlayAnyCount = false, // true for first player in turn
  selectedPlayValue = 0, // value of currently selected pieces (DEPRECATED - calculate locally)
  
  // Action props
  onPlayPieces
}) {
  const [selectedIndices, setSelectedIndices] = useState([]);
  const [showConfirmation, setShowConfirmation] = useState(false);
  
  const hasActiveTurn = currentTurnPlays.length > 0;
  const isTurnStarter = canPlayAnyCount; // canPlayAnyCount is true only for the turn starter on their first play
  const isStarterValidationRequired = isTurnStarter && !hasActiveTurn && isMyTurn;
  const selectedCards = selectedIndices.map(index => myHand[index]);
  
  // Calculate selected play value locally using same logic as GamePiece
  const calculatedSelectedValue = calculateTotalValue(selectedCards);
  
  const handleCardSelect = (index) => {
    console.log(`🎯 TURN_UI: Card clicked at index ${index}, isMyTurn: ${isMyTurn}`);
    setSelectedIndices(prev => {
      if (prev.includes(index)) {
        console.log(`🎯 TURN_UI: Deselecting card ${index}`);
        return prev.filter(i => i !== index);
      } else {
        const newSelection = [...prev, index];
        console.log(`🎯 TURN_UI: Selecting card ${index}, new selection:`, newSelection);
        // If required count is set, limit selection
        if (requiredPieceCount !== null && newSelection.length > requiredPieceCount) {
          console.log(`🎯 TURN_UI: Limited to required count ${requiredPieceCount}, replacing selection`);
          return [index]; // Replace with single selection
        }
        // First player can play 1-6 pieces
        if (isTurnStarter && newSelection.length > 6) {
          console.log(`🎯 TURN_UI: Too many cards selected for first player, keeping previous selection`);
          return prev; // Don't allow more than 6
        }
        return newSelection;
      }
    });
  };
  
  const handlePlayCards = () => {
    if (selectedIndices.length === 0) return;
    setShowConfirmation(true);
  };
  
  const handleConfirmPlay = () => {
    if (onPlayPieces && selectedIndices.length > 0) {
      onPlayPieces(selectedIndices);
      setSelectedIndices([]);
      setShowConfirmation(false);
    }
  };
  
  const handleCancelPlay = () => {
    setShowConfirmation(false);
  };
  
  const canPlay = selectedIndices.length > 0 && 
    (requiredPieceCount === null || selectedIndices.length === requiredPieceCount) &&
    (isTurnStarter ? selectedIndices.length >= 1 && selectedIndices.length <= 6 : true);

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-900 to-orange-900 p-4">
      <div className="max-w-6xl mx-auto">
        
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">
            🎮 Turn Phase
          </h1>
          <p className="text-red-200 text-lg">
            Turn {turnNumber} - {isMyTurn ? "Your turn to play" : "Waiting for other players"}
          </p>
          {/* Debug output */}
          <div className="text-xs text-yellow-300 mt-1">
            🔢 DEBUG: TurnUI received turnNumber = {turnNumber}
          </div>
          
          {requiredPieceCount !== null && (
            <div className="mt-2 inline-block bg-blue-500/20 border border-blue-500/30 rounded-lg px-3 py-1">
              <span className="text-blue-200 text-sm font-medium">
                Must play exactly {requiredPieceCount} piece{requiredPieceCount !== 1 ? 's' : ''}
              </span>
            </div>
          )}
          
          {isStarterValidationRequired && (
            <div className="mt-2 inline-block bg-yellow-500/20 border border-yellow-500/30 rounded-lg px-3 py-1">
              <span className="text-yellow-200 text-sm font-medium">
                ⚠️ As starter, your play must be valid (sets piece count for turn)
              </span>
            </div>
          )}
        </div>

        {/* Current Turn Display */}
        <div className="mb-8">
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6">
            <h2 className="text-lg font-semibold text-white mb-4 text-center">
              Current Turn Plays
            </h2>
            
            {hasActiveTurn ? (
              <div className="space-y-4">
                {currentTurnPlays.map((play, index) => (
                  <div key={index} className="border border-gray-600 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <span className="font-medium text-white">{play.player}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-300">
                          {play.cards.length} piece{play.cards.length !== 1 ? 's' : ''}
                        </span>
                        {play.isValid !== undefined && (
                          <span className={`text-xs px-2 py-1 rounded ${
                            play.isValid 
                              ? 'bg-green-500/20 text-green-300 border border-green-500/30' 
                              : 'bg-red-500/20 text-red-300 border border-red-500/30'
                          }`}>
                            {play.isValid ? 'Valid' : 'Invalid'}
                          </span>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex flex-wrap gap-2 mb-2">
                      {play.cards.map((card, cardIndex) => (
                        <GamePiece
                          key={`${play.player}-${cardIndex}`}
                          piece={card}
                          size="small"
                          className="opacity-90"
                        />
                      ))}
                    </div>
                    
                    <div className="text-sm text-gray-400">
                      Total Value: {calculateTotalValue(play.cards)}
                      {play.playType && (
                        <span className="ml-3">Type: {play.playType}</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center text-gray-400 py-8">
                <div className="text-4xl mb-2">🎯</div>
                <p>No plays yet this turn</p>
                {isTurnStarter && (
                  <p className="text-sm mt-1 text-yellow-300">
                    You set the piece count for this turn (1-6 pieces)
                  </p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* My Hand */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-white mb-4 text-center">
            My Hand
            {isMyTurn && (
              <span className="ml-2 text-green-400 text-base">
                ✨ Your Turn
              </span>
            )}
          </h2>
          
          {myHand.length > 0 ? (
            <div className="flex flex-wrap justify-center gap-2">
              {myHand.map((card, index) => (
                <GamePiece
                  key={`${card.color}-${card.point}-${index}`}
                  piece={card}
                  size="medium"
                  isSelected={selectedIndices.includes(index)}
                  isPlayable={isMyTurn}
                  onSelect={(piece) => isMyTurn && handleCardSelect(index)}
                  className={`
                    transform transition-all duration-200
                    ${isMyTurn ? 'hover:scale-105 cursor-pointer' : 'cursor-not-allowed opacity-75'}
                    ${selectedIndices.includes(index) ? 'ring-2 ring-blue-400 ring-offset-2 scale-105' : ''}
                  `}
                />
              ))}
            </div>
          ) : (
            <div className="text-center text-gray-400 py-8">
              <div className="text-4xl mb-2">🃏</div>
              <p>No cards remaining</p>
            </div>
          )}
          
          {/* Selection Info */}
          {isMyTurn && myHand.length > 0 && (
            <div className="mt-4 text-center text-sm text-red-200">
              <div>
                Selected: {selectedIndices.length} card{selectedIndices.length !== 1 ? 's' : ''}
                {requiredPieceCount !== null ? (
                  <span className="ml-2">(Need {requiredPieceCount})</span>
                ) : isTurnStarter ? (
                  <span className="ml-2">(Choose 1-6)</span>
                ) : null}
              </div>
              {selectedCards.length > 0 && (
                <div className="mt-1">
                  Total Value: {calculatedSelectedValue}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Play Interface */}
        {isMyTurn && (
          <div className="mb-8">
            <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-6">
              {!showConfirmation ? (
                <div>
                  <h3 className="text-lg font-semibold text-blue-200 mb-4 text-center">
                    {isTurnStarter ? "Set the Turn" : "Play Your Cards"}
                  </h3>
                  
                  <div className="text-center mb-6">
                    {isTurnStarter ? (
                      <div className="space-y-2">
                        <p className="text-blue-100">
                          As the first player, you can play 1-6 pieces and set the count for this turn.
                        </p>
                        <p className="text-yellow-300 text-sm">
                          ⚠️ Your play must be valid to start the turn!
                        </p>
                      </div>
                    ) : (
                      <p className="text-blue-100">
                        {requiredPieceCount 
                          ? `You must play exactly ${requiredPieceCount} piece${requiredPieceCount !== 1 ? 's' : ''}.`
                          : "Select the pieces you want to play."
                        }
                      </p>
                    )}
                  </div>
                  
                  {selectedIndices.length > 0 && (
                    <div className="mb-6">
                      <div className="bg-gray-700/50 rounded-lg p-4">
                        <h4 className="text-white font-medium mb-3">Selected Cards:</h4>
                        <div className="flex flex-wrap justify-center gap-2 mb-3">
                          {selectedCards.map((card, index) => (
                            <GamePiece
                              key={`selected-${index}`}
                              piece={card}
                              size="small"
                              className="ring-1 ring-blue-400"
                            />
                          ))}
                        </div>
                        <div className="text-sm text-gray-300 text-center">
                          Total Value: {calculatedSelectedValue}
                        </div>
                      </div>
                    </div>
                  )}
                  
                  <div className="text-center">
                    <Button
                      onClick={handlePlayCards}
                      disabled={!canPlay}
                      variant={canPlay ? "primary" : "secondary"}
                      size="large"
                      className="px-8"
                      aria-label="Play selected cards"
                    >
                      {canPlay ? "🎯 Play Cards" : 
                        selectedIndices.length === 0 ? "Select Cards to Play" :
                        isTurnStarter && selectedIndices.length > 6 ? "Too Many Cards (Max 6)" :
                        requiredPieceCount && selectedIndices.length !== requiredPieceCount ? 
                          `Need ${requiredPieceCount} Cards` : "Invalid Selection"
                      }
                    </Button>
                    
                    {selectedIndices.length > 0 && (
                      <button
                        onClick={() => setSelectedIndices([])}
                        className="ml-4 text-gray-300 hover:text-white text-sm underline transition-colors"
                        aria-label="Clear selection"
                      >
                        Clear Selection
                      </button>
                    )}
                  </div>
                </div>
              ) : (
                <div className="text-center">
                  <h3 className="text-lg font-semibold text-blue-200 mb-4">
                    Confirm Your Play
                  </h3>
                  
                  <div className="mb-6">
                    <div className="bg-gray-700/50 rounded-lg p-4 mb-4">
                      <div className="flex flex-wrap justify-center gap-2 mb-3">
                        {selectedCards.map((card, index) => (
                          <GamePiece
                            key={`confirm-${index}`}
                            piece={card}
                            size="medium"
                            className="ring-2 ring-green-400"
                          />
                        ))}
                      </div>
                      <div className="text-white font-medium">
                        Playing {selectedCards.length} card{selectedCards.length !== 1 ? 's' : ''} 
                        (Total Value: {calculatedSelectedValue})
                      </div>
                      {isTurnStarter && (
                        <div className="text-yellow-300 text-sm mt-2">
                          This will set the piece count to {selectedCards.length} for all players this turn
                        </div>
                      )}
                    </div>
                    
                    <p className="text-blue-100">
                      Confirm this play?
                    </p>
                  </div>
                  
                  <div className="flex justify-center gap-4">
                    <Button
                      onClick={handleConfirmPlay}
                      variant="success"
                      size="large"
                      className="px-8"
                      aria-label="Confirm play"
                    >
                      ✅ Confirm Play
                    </Button>
                    
                    <Button
                      onClick={handleCancelPlay}
                      variant="secondary"
                      size="large"
                      className="px-8"
                      aria-label="Cancel play"
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
        {!isMyTurn && (
          <div className="mb-8">
            <div className="bg-gray-500/10 border border-gray-500/20 rounded-xl p-6 text-center">
              <div className="text-gray-300 mb-4">
                Waiting for other players to play...
              </div>
              <div className="flex justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-red-400"></div>
              </div>
            </div>
          </div>
        )}

        {/* Status Footer */}
        <div className="text-center text-sm text-red-300">
          <div>Turn {turnNumber} - {currentTurnPlays.length} player{currentTurnPlays.length !== 1 ? 's' : ''} played</div>
          {requiredPieceCount !== null && (
            <div>Required pieces: {requiredPieceCount}</div>
          )}
          {isTurnStarter && !hasActiveTurn && (
            <div className="text-yellow-300">You must make a valid play to start the turn</div>
          )}
        </div>
      </div>
    </div>
  );
}

// No helper functions needed - all calculations done by backend

// PropTypes definition
TurnUI.propTypes = {
  // Data props
  myHand: PropTypes.arrayOf(PropTypes.shape({
    color: PropTypes.string.isRequired,
    point: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
    kind: PropTypes.string.isRequired
  })),
  currentTurnPlays: PropTypes.arrayOf(PropTypes.shape({
    player: PropTypes.string.isRequired,
    cards: PropTypes.arrayOf(PropTypes.shape({
      color: PropTypes.string.isRequired,
      point: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
      kind: PropTypes.string.isRequired
    })).isRequired,
    isValid: PropTypes.bool,
    playType: PropTypes.string,
    totalValue: PropTypes.number
  })),
  requiredPieceCount: PropTypes.number,
  turnNumber: PropTypes.number,
  
  // State props (calculated by backend)
  isMyTurn: PropTypes.bool,
  canPlayAnyCount: PropTypes.bool,
  selectedPlayValue: PropTypes.number,
  
  // Action props
  onPlayPieces: PropTypes.func
};

TurnUI.defaultProps = {
  myHand: [],
  currentTurnPlays: [],
  requiredPieceCount: null,
  turnNumber: 1,
  isMyTurn: false,
  canPlayAnyCount: false,
  selectedPlayValue: 0,
  onPlayPieces: () => {}
};

export default TurnUI;