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
  playType = '',
  declarationData = {},
  playerHandSizes = {},
  animationPending = false,
  
  // State flags
  isMyTurn = false,
  canPlayAnyCount = false,
  
  // Action props
  onPlayPieces,
  onPass,
  onAnimationComplete
}) {
  // Build player pieces from turn plays
  const playerPieces = {};
  currentTurnPlays.forEach(play => {
    if (play.player && play.cards) {
      // Use cards property from the converted turn plays
      playerPieces[play.player] = play.cards;
    }
  });
  
  // Extract play type from the current turn plays
  const currentPlayType = playType || (() => {
    const validPlays = currentTurnPlays.filter(play => play.isValid !== false);
    if (validPlays.length > 0) {
      const lastPlay = validPlays[validPlays.length - 1];
      // Check both camelCase and snake_case
      return lastPlay.playType || lastPlay.play_type || '';
    }
    return '';
  })();
  
  // Build player stats from declaration and piles won
  const playerStats = {};
  players.forEach(player => {
    playerStats[player.name] = {
      pilesWon: piecesWonCount[player.name] || 0,
      declared: declarationData[player.name] || 0
    };
  });
  
  // Use current pile from props or derive from currentTurnPlays
  const pile = currentPile.length > 0 ? currentPile : 
    currentTurnPlays.reduce((acc, play) => [...acc, ...(play.cards || [])], []);
  
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
      playType={currentPlayType}
      playerStats={playerStats}
      playerHandSizes={playerHandSizes}
      animationPending={animationPending}
      onPlayPieces={onPlayPieces}
      onPass={onPass}
      onAnimationComplete={onAnimationComplete}
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
  playType: PropTypes.string,
  declarationData: PropTypes.object,
  playerHandSizes: PropTypes.object,
  animationPending: PropTypes.bool,
  
  // State flags
  isMyTurn: PropTypes.bool,
  canPlayAnyCount: PropTypes.bool,
  
  // Actions
  onPlayPieces: PropTypes.func,
  onPass: PropTypes.func,
  onAnimationComplete: PropTypes.func
};

export default TurnUI;