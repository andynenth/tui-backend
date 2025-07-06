/**
 * 🎮 **TurnUI Component** - Mockup-Accurate Turn Phase Interface
 * 
 * This component implements the exact design from turn-ui-mockup.html
 * with all the specific CSS classes and structure.
 */

import React, { useState } from 'react';
import PropTypes from 'prop-types';
import EnhancedGamePiece from '../shared/EnhancedGamePiece';

export function TurnUI({
  // Data props
  myHand = [],
  currentTurnPlays = [],
  requiredPieceCount = null,
  turnNumber = 1,
  
  // State props
  isMyTurn = false,
  canPlayAnyCount = false,
  currentPlayer = 'Alice',
  players = [
    { name: 'Alice', is_bot: false },
    { name: 'Bot_Charlie', is_bot: true },
    { name: 'Bot_David', is_bot: true },
    { name: 'Bot_Eve', is_bot: true }
  ],
  
  // Action props
  onPlayPieces
}) {
  const [selectedIndices, setSelectedIndices] = useState([]);
  const [showConfirmPanel, setShowConfirmPanel] = useState(false);
  
  const selectedPieces = selectedIndices.map(i => myHand[i]);
  const totalValue = selectedPieces.reduce((sum, piece) => sum + (piece.point || 0), 0);
  
  // Get player status
  const getPlayerStatus = (playerName) => {
    if (playerName === currentPlayer && isMyTurn) return 'current';
    const hasPlayed = currentTurnPlays.some(play => play.player === playerName);
    return hasPlayed ? 'played' : 'waiting';
  };
  
  // Handle piece selection
  const handlePieceSelect = (index) => {
    if (!isMyTurn) return;
    
    setSelectedIndices(prev => {
      if (prev.includes(index)) {
        return prev.filter(i => i !== index);
      } else {
        const newSelection = [...prev, index];
        // Limit selection based on requirements
        if (requiredPieceCount && newSelection.length > requiredPieceCount) {
          return [index];
        }
        if (canPlayAnyCount && newSelection.length > 6) {
          return prev;
        }
        return newSelection;
      }
    });
    
    // Show confirm panel when pieces are selected
    if (!selectedIndices.includes(index) && selectedIndices.length === 0) {
      setTimeout(() => setShowConfirmPanel(true), 300);
    }
  };
  
  const handleConfirmPlay = () => {
    if (onPlayPieces && selectedIndices.length > 0) {
      onPlayPieces(selectedIndices);
      setSelectedIndices([]);
      setShowConfirmPanel(false);
    }
  };
  
  const handleCancelPlay = () => {
    setSelectedIndices([]);
    setShowConfirmPanel(false);
  };
  
  const canPlay = selectedIndices.length > 0 && 
    (!requiredPieceCount || selectedIndices.length === requiredPieceCount);

  return (
    <div className="game-container">
      {/* Turn Number Indicator */}
      <div className="turn-indicator">
        Turn {turnNumber}
      </div>
      
      {/* Phase Header */}
      <div className="phase-header">
        <div className="phase-title">Turn Phase</div>
        <div className="phase-subtitle">
          {isMyTurn ? "Your turn to play pieces" : `Waiting for ${currentPlayer}`}
        </div>
        {isMyTurn && (
          <div className="turn-status">Your Turn</div>
        )}
      </div>
      
      {/* Game Status Section */}
      <div className="game-status-section">
        {/* Turn Requirement */}
        {requiredPieceCount && (
          <div className="turn-requirement">
            Must play exactly {requiredPieceCount} piece{requiredPieceCount !== 1 ? 's' : ''}
          </div>
        )}
        
        {canPlayAnyCount && !currentTurnPlays.length && (
          <div className="turn-requirement">
            You choose: Play 1-6 pieces
          </div>
        )}
        
        {/* Players List */}
        <div className="players-list">
          {players.map((player) => {
            const status = getPlayerStatus(player.name);
            const playerPlay = currentTurnPlays.find(play => play.player === player.name);
            
            return (
              <div key={player.name} className={`player-row ${status}`}>
                <div className="player-avatar">
                  {player.name.charAt(0)}
                </div>
                <div className="player-info">
                  <div className="player-name">{player.name}</div>
                  {playerPlay && (
                    <div className="text-xs text-gray-500">
                      {playerPlay.cards.length} pieces • {playerPlay.totalValue} pts
                    </div>
                  )}
                </div>
                <div className="player-status">
                  <span className={`status-badge ${status}`}>
                    {status === 'current' ? 'Playing' : 
                     status === 'played' ? 'Done' : 'Waiting'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
        
        {/* Waiting State */}
        {!isMyTurn && (
          <div className="waiting-state">
            <div className="waiting-spinner"></div>
            <div className="text-sm text-gray-500">
              Waiting for {currentPlayer} to play...
            </div>
          </div>
        )}
      </div>
      
      {/* Confirm Selection Panel */}
      <div className={`confirm-panel ${showConfirmPanel && selectedIndices.length > 0 ? 'show' : ''}`}>
        <div className="selection-info">
          <div className="selection-count">
            {selectedIndices.length} piece{selectedIndices.length !== 1 ? 's' : ''} selected
          </div>
          <div className="text-xs text-gray-600 mt-1">
            Total value: {totalValue} points
          </div>
        </div>
        
        <div className="action-buttons">
          <button 
            className="action-button"
            onClick={handleConfirmPlay}
          >
            Play
          </button>
          <button 
            className="action-button secondary"
            onClick={handleCancelPlay}
          >
            Cancel
          </button>
        </div>
      </div>
      
      {/* Player Hand Section */}
      <div className="hand-section">
        <div className="pieces-tray">
          {myHand.map((piece, index) => (
            <EnhancedGamePiece
              key={index}
              piece={piece}
              isSelected={selectedIndices.includes(index)}
              onClick={() => handlePieceSelect(index)}
              disabled={!isMyTurn}
              animationDelay={`${index * 0.1}s`}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

TurnUI.propTypes = {
  myHand: PropTypes.arrayOf(PropTypes.shape({
    color: PropTypes.oneOf(['red', 'black']).isRequired,
    character: PropTypes.string,
    display: PropTypes.string,
    point: PropTypes.number,
    value: PropTypes.number
  })),
  currentTurnPlays: PropTypes.arrayOf(PropTypes.shape({
    player: PropTypes.string.isRequired,
    cards: PropTypes.array.isRequired,
    totalValue: PropTypes.number
  })),
  requiredPieceCount: PropTypes.number,
  turnNumber: PropTypes.number,
  isMyTurn: PropTypes.bool,
  canPlayAnyCount: PropTypes.bool,
  currentPlayer: PropTypes.string,
  players: PropTypes.arrayOf(PropTypes.shape({
    name: PropTypes.string.isRequired,
    is_bot: PropTypes.bool
  })),
  onPlayPieces: PropTypes.func
};

export default TurnUI;