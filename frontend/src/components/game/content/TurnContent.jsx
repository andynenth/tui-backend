import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { getPieceDisplay, getPieceColorClass, formatPieceValue } from '../../../utils/pieceMapping';

/**
 * TurnContent Component
 * 
 * Displays the turn phase with:
 * - Circular table layout with player positions
 * - Current pile in center
 * - Player pieces around table
 * - Selected pieces display
 * - Play/Pass actions
 */
const TurnContent = ({
  myHand = [],
  players = [],
  currentPlayer = '',
  myName = '',
  currentPile = [],
  requiredPieceCount = 0,
  turnNumber = 1,
  playerPieces = {}, // { playerName: pieces[] }
  lastWinner = '',
  onPlayPieces,
  onPass
}) => {
  const [selectedPieces, setSelectedPieces] = useState([]);
  
  // Check if it's my turn
  const isMyTurn = currentPlayer === myName;
  
  // Get player position (0-3)
  const getPlayerPosition = (playerName) => {
    const index = players.findIndex(p => p.name === playerName);
    return index;
  };
  
  // Map position index to position class
  const getPositionClass = (index) => {
    const positions = ['bottom', 'right', 'top', 'left'];
    return positions[index] || 'bottom';
  };
  
  // Handle piece selection
  const handlePieceSelect = (piece, index) => {
    if (!isMyTurn) return;
    
    const pieceId = `${index}-${piece.type}-${piece.color}`;
    
    if (selectedPieces.some(p => p.id === pieceId)) {
      // Deselect
      setSelectedPieces(selectedPieces.filter(p => p.id !== pieceId));
    } else {
      // Select
      setSelectedPieces([...selectedPieces, { ...piece, id: pieceId, index }]);
    }
  };
  
  // Check if can play
  const canPlay = () => {
    if (!isMyTurn) return false;
    if (requiredPieceCount === 0) return selectedPieces.length > 0;
    return selectedPieces.length === requiredPieceCount;
  };
  
  // Handle play
  const handlePlay = () => {
    if (canPlay() && onPlayPieces) {
      const pieceIndices = selectedPieces.map(p => p.index);
      onPlayPieces(pieceIndices);
      setSelectedPieces([]);
    }
  };
  
  // Handle pass
  const handlePass = () => {
    if (isMyTurn && onPass) {
      onPass();
      setSelectedPieces([]);
    }
  };
  
  // Get turn requirement message
  const getTurnRequirement = () => {
    if (!isMyTurn) {
      return { type: 'waiting', text: `Waiting for ${currentPlayer} to play` };
    }
    
    if (requiredPieceCount === 0) {
      return { type: 'active', text: 'Play any number of pieces or pass' };
    }
    
    return { type: 'active', text: `Must play exactly ${requiredPieceCount} piece${requiredPieceCount > 1 ? 's' : ''}` };
  };
  
  const requirement = getTurnRequirement();
  
  return (
    <>
      {/* Turn indicator */}
      <div className="turn-indicator">
        Turn {turnNumber}
      </div>
      
      {/* Modified phase header for turn info */}
      <div className="gl-phase-header">
        <h1 className="gl-phase-title">Game Time</h1>
        <p className="gl-phase-subtitle">Play your pieces strategically</p>
        <div className={`turn-requirement ${requirement.type}`}>
          {requirement.text}
        </div>
      </div>
      
      {/* Table section */}
      <div className="turn-table-section">
        <div className="turn-table-layout">
          {/* Central table */}
          <div className="turn-central-table">
            <div className="turn-current-pile">
              <div className="turn-pile-label">Current Pile</div>
              <div className="turn-pile-display">
                {currentPile.length === 0 ? (
                  <div className="turn-empty-pile">Empty</div>
                ) : (
                  currentPile.map((piece, idx) => (
                    <div 
                      key={idx}
                      className={`turn-mini-piece ${getPieceColorClass(piece)}`}
                    >
                      {getPieceDisplay(piece)}
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
          
          {/* Player seats and pieces */}
          {players.map((player, index) => {
            const position = getPositionClass(index);
            const isActive = player.name === currentPlayer;
            const isWinner = player.name === lastWinner;
            const pieces = playerPieces[player.name] || [];
            
            return (
              <React.Fragment key={player.name}>
                {/* Player seat */}
                <div className={`turn-player-seat position-${position} ${isActive ? 'active' : ''} ${isWinner ? 'winner' : ''}`}>
                  <div className="turn-player-name">
                    {player.name}{player.name === myName ? ' (You)' : ''}
                  </div>
                  <div className="turn-player-status">
                    {pieces.length} pieces
                  </div>
                </div>
                
                {/* Player pieces (only show for current player) */}
                {isActive && pieces.length > 0 && (
                  <div className={`turn-player-pieces position-${position}`}>
                    {pieces.slice(0, 6).map((piece, idx) => (
                      <div 
                        key={idx}
                        className={`turn-mini-piece ${getPieceColorClass(piece)}`}
                      >
                        {getPieceDisplay(piece)}
                      </div>
                    ))}
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>
      
      {/* Action section */}
      <div className="turn-action-section">
        {/* Selected pieces display */}
        <div className="turn-selected-display">
          <div className="turn-selected-label">Selected Pieces</div>
          {selectedPieces.length === 0 ? (
            <div className="turn-no-selection">
              {isMyTurn ? 'Select pieces to play' : 'Not your turn'}
            </div>
          ) : (
            <div className="turn-selected-pieces">
              {selectedPieces.map((piece) => (
                <div 
                  key={piece.id}
                  className={`piece ${getPieceColorClass(piece)}`}
                  style={{ width: '40px', height: '40px' }}
                >
                  <div className="piece-character" style={{ fontSize: '14px' }}>
                    {getPieceDisplay(piece)}
                  </div>
                  <div className="piece-points" style={{ fontSize: '8px' }}>
                    {formatPieceValue(piece)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        
        {/* Action buttons */}
        <div className="turn-actions">
          <button
            className="turn-action-btn primary"
            onClick={handlePlay}
            disabled={!canPlay()}
          >
            Play
          </button>
          <button
            className="turn-action-btn secondary"
            onClick={handlePass}
            disabled={!isMyTurn}
          >
            Pass
          </button>
        </div>
      </div>
      
      {/* Hand section - always visible at bottom */}
      <div className="hand-section">
        <div className="pieces-tray">
          {myHand.map((piece, index) => {
            const pieceId = `${index}-${piece.type}-${piece.color}`;
            const isSelected = selectedPieces.some(p => p.id === pieceId);
            
            return (
              <div 
                key={index}
                className={`piece ${getPieceColorClass(piece)} ${isSelected ? 'selected' : ''} ${isMyTurn ? 'clickable' : ''}`}
                onClick={() => handlePieceSelect(piece, index)}
                style={{
                  cursor: isMyTurn ? 'pointer' : 'default',
                  transform: isSelected ? 'translateY(-8px) scale(1.05)' : '',
                  boxShadow: isSelected ? '0 8px 16px rgba(255, 193, 7, 0.3)' : '',
                  border: isSelected ? '3px solid #FFC107' : ''
                }}
              >
                <div className="piece-character">
                  {getPieceDisplay(piece)}
                </div>
                <div className="piece-points">
                  {formatPieceValue(piece)}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </>
  );
};

TurnContent.propTypes = {
  myHand: PropTypes.array,
  players: PropTypes.array,
  currentPlayer: PropTypes.string,
  myName: PropTypes.string,
  currentPile: PropTypes.array,
  requiredPieceCount: PropTypes.number,
  turnNumber: PropTypes.number,
  playerPieces: PropTypes.object,
  lastWinner: PropTypes.string,
  onPlayPieces: PropTypes.func,
  onPass: PropTypes.func
};

export default TurnContent;