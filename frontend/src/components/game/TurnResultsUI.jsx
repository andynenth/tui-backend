/**
 * 🏆 **TurnResultsUI Component** - Turn Results Interface
 *
 * Features:
 * ✅ Uses new TurnResultsContent for consistent UI
 * ✅ Maps game state to content props
 * ✅ Handles auto-advance timer
 */

import React from 'react';
import PropTypes from 'prop-types';
import TurnResultsContent from './content/TurnResultsContent';

/**
 * TurnResultsUI - wrapper for TurnResultsContent
 */
export function TurnResultsUI({
  // Data props
  winner = '',
  winningPlay = null,
  playerPiles = {},
  players = [],
  turnNumber = 1,
  roundNumber = 1,
  nextStarter = '',
  playerName = '',
  isLastTurn = false,
  currentTurnPlays = [], // Turn plays data from turn phase

  // Action props
  onContinue,
}) {
  // Extract winning pieces from winning play
  const winningPieces = winningPlay?.pieces || [];

  // Build player plays array from turn plays data
  // The currentTurnPlays should contain what each player played
  console.log(
    '[TurnResultsUI] Building playerPlays from currentTurnPlays:',
    currentTurnPlays
  );

  // Log details of each play
  currentTurnPlays.forEach((play, index) => {
    console.log(`[TurnResultsUI] Turn play ${index + 1}:`, {
      player: play.player,
      hasPieces: !!play.pieces,
      hasCards: !!play.cards,
      playType: play.playType || play.play_type,
      isValid: play.isValid,
      isStarter: play.isStarter,
      pieces: play.pieces ? JSON.stringify(play.pieces) : 'null',
      cards: play.cards ? JSON.stringify(play.cards) : 'null',
    });
  });

  const playerPlays = players.map((player) => {
    // Find what this player played in the turn
    const turnPlay = currentTurnPlays.find(
      (play) => play.player === player.name
    );
    return {
      playerName: player.name,
      player, // Include full player object for captured/declared data
      pieces: turnPlay?.pieces || turnPlay?.cards || [],
    };
  });

  // Find the starter and their play type
  const starterPlay = currentTurnPlays.find(
    (play) => play.isStarter || play.player === winningPlay?.starter
  );
  const starterName = starterPlay?.player || winner;
  const starterPlayType =
    starterPlay?.playType || starterPlay?.play_type || winningPlay?.type || '';

  console.log('[TurnResultsUI] Extracting starter info:', {
    currentTurnPlays,
    starterPlay,
    starterName,
    starterPlayType,
    winningPlay,
  });

  // Pass through props to TurnResultsContent
  return (
    <TurnResultsContent
      winner={winner}
      winningPieces={winningPieces}
      playerPlays={playerPlays}
      myName={playerName}
      turnNumber={turnNumber}
      roundNumber={roundNumber}
      isLastTurn={isLastTurn}
      nextStarter={nextStarter}
      starterPlayType={starterPlayType}
      starterName={starterName}
      onContinue={onContinue}
    />
  );
}

TurnResultsUI.propTypes = {
  // Data props
  winner: PropTypes.string,
  winningPlay: PropTypes.shape({
    pieces: PropTypes.array,
    value: PropTypes.number,
    type: PropTypes.string,
    pilesWon: PropTypes.number,
  }),
  playerPiles: PropTypes.object,
  players: PropTypes.array,
  turnNumber: PropTypes.number,
  roundNumber: PropTypes.number,
  nextStarter: PropTypes.string,
  playerName: PropTypes.string,
  isLastTurn: PropTypes.bool,
  currentTurnPlays: PropTypes.array,

  // Actions
  onContinue: PropTypes.func,
};

export default TurnResultsUI;
