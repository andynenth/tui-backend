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
  onContinue
}) {
  // Extract winning pieces from winning play
  const winningPieces = winningPlay?.pieces || [];
  
  // Build player plays array from turn plays data
  // The currentTurnPlays should contain what each player played
  const playerPlays = players.map(player => {
    // Find what this player played in the turn
    const turnPlay = currentTurnPlays.find(play => play.player === player.name);
    return {
      playerName: player.name,
      pieces: turnPlay?.pieces || turnPlay?.cards || []
    };
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
    pilesWon: PropTypes.number
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
  onContinue: PropTypes.func
};

export default TurnResultsUI;