/**
 * 🎲 **TurnUI Component** - Turn Phase Interface
 *
 * Features:
 * ✅ Uses new TurnContent for consistent UI
 * ✅ Maps game state to content props
 * ✅ Handles turn actions (play/pass)
 * ✅ Migrated to StyleX
 */

import React from 'react';
import PropTypes from 'prop-types';
import TurnContent from './content/TurnContent';

/**
 * TurnUI - wrapper for TurnContent
 * This component primarily handles data transformation and doesn't have its own styles
 */
export function TurnUI({
  // Game state data
  myHand = [],
  players = [],
  currentPlayer = ',
  playerName = ',
  currentPile = [],
  requiredPieceCount = 0,
  turnNumber = 1,
  piecesWonCount = {},
  previousWinner = ',
  currentTurnPlays = [],
  playType = ',
  declarationData = {},
  playerHandSizes = {},

  // State flags
  isMyTurn = false,
  canPlayAnyCount = false,

  // Action props
  onPlayPieces,
  onPass,
}) {
  // Build player pieces from turn plays
  const playerPieces = {};
  console.log(
    '[TurnUI] Building playerPieces from currentTurnPlays:',
    currentTurnPlays
  );

  // Log details of each play
  currentTurnPlays.forEach((play, index) => {
    console.log(`[TurnUI] Turn play ${index + 1}:`, {
      player: play.player,
      hasPieces: !!play.pieces,
      hasCards: !!play.cards,
      playType: play.playType || play.play_type,
      isValid: play.isValid,
      pieces: play.pieces ? JSON.stringify(play.pieces) : 'null',
      cards: play.cards ? JSON.stringify(play.cards) : 'null',
    });
  });

  currentTurnPlays.forEach((play) => {
    if (play.player && (play.pieces || play.cards)) {
      // Use pieces property (or cards for backward compatibility)
      playerPieces[play.player] = play.pieces || play.cards;
    }
  });

  // Extract play type from the current turn plays
  const currentPlayType =
    playType ||
    (() => {
      const validPlays = currentTurnPlays.filter(
        (play) => play.isValid !== false
      );
      if (validPlays.length > 0) {
        const lastPlay = validPlays[validPlays.length - 1];
        // Check both camelCase and snake_case
        const extractedType = lastPlay.playType || lastPlay.play_type || ';
        console.log('[TurnUI] Extracting play type:', {
          playType,
          currentTurnPlays,
          validPlays,
          lastPlay,
          extractedType,
        });
        return extractedType;
      }
      console.log('[TurnUI] No valid plays found, returning empty play type');
      return ';
    })();

  // Build player stats from declaration and piles won
  const playerStats = {};
  players.forEach((player) => {
    playerStats[player.name] = {
      pilesWon: piecesWonCount[player.name] || 0,
      declared: declarationData[player.name] || 0,
    };
  });

  // Use current pile from props or derive from currentTurnPlays
  const pile =
    currentPile.length > 0
      ? currentPile
      : currentTurnPlays.reduce(
          (acc, play) => [...acc, ...(play.pieces || play.cards || [])],
          []
        );

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
  playType: PropTypes.string,
  declarationData: PropTypes.object,
  playerHandSizes: PropTypes.object,

  // State flags
  isMyTurn: PropTypes.bool,
  canPlayAnyCount: PropTypes.bool,

  // Actions
  onPlayPieces: PropTypes.func,
  onPass: PropTypes.func,
};

export default TurnUI;