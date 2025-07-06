/**
 * 🎮 **TableTurnUI** - Table-based Turn Phase UI matching turn-ui-table-variation2.html
 * 
 * Features:
 * ✅ Central game table with grid pattern
 * ✅ Player positions around table (top, bottom, left, right)
 * ✅ Visual piece display on table
 * ✅ Player summary bars with compact info
 * ✅ Immersive table-based layout
 */

import React from 'react';
import PropTypes from 'prop-types';
import EnhancedGamePiece from '../shared/EnhancedGamePiece';

export function TableTurnUI({
  players = [],
  currentPlayer = '',
  isMyTurn = false,
  currentTurnPlays = [],
  requiredPieceCount = null,
  canPlayAnyCount = false,
  turnNumber = 1,
  myHand = [],
  selectedPieces = [],
  showConfirmPanel = false,
  onPieceSelect,
  onConfirmPlay,
  onCancelSelection
}) {
  // Map players to table positions (top, right, bottom, left)
  const getPlayerPosition = (index, totalPlayers) => {
    const positions = ['bottom', 'right', 'top', 'left'];
    return positions[index % 4];
  };

  // Get player by position
  const getPlayerByPosition = (position) => {
    const index = ['bottom', 'right', 'top', 'left'].indexOf(position);
    return players[index] || null;
  };

  // Get pieces played by a player
  const getPlayerPieces = (playerName) => {
    const play = currentTurnPlays.find(p => p.player === playerName);
    return play ? play.pieces : [];
  };

  // Get turn requirement message
  const getTurnRequirement = () => {
    if (!isMyTurn) {
      return { text: `Waiting for ${currentPlayer} to play`, className: 'waiting' };
    }
    if (requiredPieceCount) {
      return { text: `Must play exactly ${requiredPieceCount} piece${requiredPieceCount !== 1 ? 's' : ''}`, className: '' };
    }
    if (canPlayAnyCount) {
      return { text: 'You choose: Play 1-6 pieces', className: '' };
    }
    return { text: 'Your turn to play', className: '' };
  };

  const requirement = getTurnRequirement();

  // Get player stats (declarations)
  const getPlayerStats = (player) => {
    // This would come from declarations - for now showing placeholder
    const declared = player.declaration || 0;
    const won = player.pilesWon || 0;
    return { declared, won };
  };

  return (
    <div className="game-container">
      <div className="table-turn-container">
        {/* Turn indicator */}
        <div className="turn-indicator">Turn {turnNumber}</div>

        {/* Phase header */}
        <div className="phase-header">
          <div className="phase-title">Turn Phase</div>
          <div className="phase-subtitle">{isMyTurn ? 'Your turn to play pieces' : `${currentPlayer}'s Turn`}</div>
          <div className={`turn-requirement-header ${requirement.className}`}>
            {requirement.text}
          </div>
        </div>

        {/* Table section */}
        <div className="table-section">
        <div className="table-layout">
          {/* Central table */}
          <div className="central-table">
            {/* Player pieces areas */}
            {['top', 'right', 'bottom', 'left'].map(position => {
              const player = getPlayerByPosition(position);
              if (!player) return null;
              
              const pieces = getPlayerPieces(player.name);
              const hasPlayed = pieces.length > 0;
              
              return (
                <div 
                  key={position}
                  className={`player-pieces-area ${position} ${pieces.length <= 3 ? 'single-line' : ''}`}
                >
                  {pieces.map((piece, idx) => (
                    <div key={idx} className="table-piece flipped">
                      <div className="table-piece-face table-piece-back"></div>
                      <div className={`table-piece-face table-piece-front ${piece.color}`}>
                        {piece.character || '?'}
                      </div>
                    </div>
                  ))}
                </div>
              );
            })}
          </div>

          {/* Player summary bars */}
          {['top', 'right', 'bottom', 'left'].map(position => {
            const player = getPlayerByPosition(position);
            if (!player) return null;
            
            const stats = getPlayerStats(player);
            const hasPlayed = currentTurnPlays.some(p => p.player === player.name);
            const isActive = player.name === currentPlayer;
            const isCurrentUser = player.isMe;
            
            return (
              <div 
                key={position}
                className={`player-summary-bar ${position} ${isActive ? 'active' : ''} ${hasPlayed ? 'played' : ''} ${isCurrentUser ? 'current-user' : ''}`}
              >
                <div className="player-summary-content">
                  <div className="player-avatar-small">{player.name.charAt(0)}</div>
                  <span className="player-name-short">{player.name}</span>
                  <div className="player-stats-compact">
                    <span className="stat-number">{stats.won}</span>
                    <span className="stat-separator">/</span>
                    <span className="stat-number">{stats.declared}</span>
                  </div>
                </div>
                <div className="status-icons">
                  {/* Status dots - could represent pieces or piles won */}
                  {[...Array(6)].map((_, i) => (
                    <span key={i} className="status-icon"></span>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
        </div>

        {/* Confirm panel */}
        <div className={`confirm-panel ${showConfirmPanel && selectedPieces.length > 0 ? 'show' : ''}`}>
          <div className="selection-info">
          <div className="selection-count">
            {selectedPieces.length} piece{selectedPieces.length !== 1 ? 's' : ''} selected
          </div>
          <div className="selection-value">
            Total value: {selectedPieces.reduce((sum, i) => sum + (myHand[i]?.point || 0), 0)} points
          </div>
        </div>
        
        <div className="action-buttons">
          <button className="action-button" onClick={onConfirmPlay}>
            Play Cards
          </button>
          <button className="action-button secondary" onClick={onCancelSelection}>
            Clear
          </button>
        </div>
        </div>

        {/* Hand section */}
        <div className={`hand-section ${isMyTurn ? 'active-turn' : ''}`}>
        <div className="pieces-tray">
          {myHand.map((piece, index) => (
            <EnhancedGamePiece
              key={index}
              piece={piece}
              isSelected={selectedPieces.includes(index)}
              onClick={() => onPieceSelect(index)}
              disabled={!isMyTurn}
              animationDelay={`${index * 0.1}s`}
            />
          ))}
        </div>
      </div>
    </div>
    </div>
  );
}

TableTurnUI.propTypes = {
  players: PropTypes.arrayOf(PropTypes.shape({
    name: PropTypes.string.isRequired,
    isMe: PropTypes.bool,
    declaration: PropTypes.number,
    pilesWon: PropTypes.number
  })),
  currentPlayer: PropTypes.string,
  isMyTurn: PropTypes.bool,
  currentTurnPlays: PropTypes.arrayOf(PropTypes.shape({
    player: PropTypes.string,
    pieces: PropTypes.array
  })),
  requiredPieceCount: PropTypes.number,
  canPlayAnyCount: PropTypes.bool,
  turnNumber: PropTypes.number,
  myHand: PropTypes.array,
  selectedPieces: PropTypes.array,
  showConfirmPanel: PropTypes.bool,
  onPieceSelect: PropTypes.func,
  onConfirmPlay: PropTypes.func,
  onCancelSelection: PropTypes.func
};

export default TableTurnUI;