/**
 * 🎲 **TurnUI Component** - Turn Phase Interface
 * 
 * Features:
 * ✅ Uses new TurnContent for consistent UI
 * ✅ Maps game state to content props
 * ✅ Handles turn actions (play/pass)
 */

import React from 'react';
import PropTypes from 'prop-types';
import TurnContent from './content/TurnContent';

/**
 * TurnUI - wrapper for TurnContent
 */
export function TurnUI({
  // Game state data
  myHand = [],
  players = [],
  currentPlayer = '',
  playerName = '',
  currentPile = [],
  requiredPieceCount = 0,
  turnNumber = 1,
  piecesWonCount = {},
  previousWinner = '',
  currentTurnPlays = [],
  
  // State flags
  isMyTurn = false,
  canPlayAnyCount = false,
  
  // Action props
  onPlayPieces,
  onPass
}) {
  // Calculate player pieces count for display
  const playerPieces = {};
  players.forEach(player => {
    const won = piecesWonCount[player.name] || 0;
    const handSize = player.name === playerName ? myHand.length : 8; // Assume others have pieces
    playerPieces[player.name] = Array(handSize).fill({ type: 'UNKNOWN', color: 'black' });
  });
  
  // Use current pile from props or derive from currentTurnPlays
  const pile = currentPile.length > 0 ? currentPile : 
    currentTurnPlays.reduce((acc, play) => [...acc, ...play.pieces], []);
  
  // Determine required count
  const required = canPlayAnyCount ? 0 : requiredPieceCount;
  
  // Pass through props to TurnContent
  return (
    <TurnContent 
      myHand={myHand}
      players={players}
      currentPlayer={currentPlayer}
      myName={playerName}
      currentPile={pile}
      requiredPieceCount={required}
      turnNumber={turnNumber}
      playerPieces={playerPieces}
      lastWinner={previousWinner}
      onPlayPieces={onPlayPieces}
      onPass={onPass}
    />
  );
}

TurnUI.propTypes = {
  // Game state
  myHand: PropTypes.array,
  players: PropTypes.array,
  currentPlayer: PropTypes.string,
  playerName: PropTypes.string,
  currentPile: PropTypes.array,
  requiredPieceCount: PropTypes.number,
  turnNumber: PropTypes.number,
  piecesWonCount: PropTypes.object,
  previousWinner: PropTypes.string,
  currentTurnPlays: PropTypes.array,
  
  // State flags
  isMyTurn: PropTypes.bool,
  canPlayAnyCount: PropTypes.bool,
  
  // Actions
  onPlayPieces: PropTypes.func,
  onPass: PropTypes.func
};

export default TurnUI;