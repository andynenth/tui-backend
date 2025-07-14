/**
 * 🎯 **DeclarationUI Component** - Declaration Phase Interface
 *
 * Features:
 * ✅ Uses new DeclarationContent for consistent UI
 * ✅ Maps game state to content props
 * ✅ Handles declaration actions
 */

import React from 'react';
import PropTypes from 'prop-types';
import DeclarationContent from './content/DeclarationContent';

/**
 * DeclarationUI - wrapper for DeclarationContent
 */
export function DeclarationUI({
  // Data props
  myHand = [],
  declarations = {},
  players = [],
  currentTotal = 0,

  // State props
  isMyTurn = false,
  validOptions = [],
  declarationProgress = { declared: 0, total: 4 },
  isLastPlayer = false,
  estimatedPiles = 0,
  handStrength = 0,
  currentPlayer = '',
  myName = '',
  consecutiveZeros = 0,
  redealMultiplier = 1,

  // Action props
  onDeclare,
}) {
  // Simply pass through props to DeclarationContent
  return (
    <DeclarationContent
      myHand={myHand}
      players={players}
      currentPlayer={currentPlayer}
      myName={myName}
      declarations={declarations}
      totalDeclared={currentTotal}
      consecutiveZeros={consecutiveZeros}
      redealMultiplier={redealMultiplier}
      onDeclare={onDeclare}
    />
  );
}

DeclarationUI.propTypes = {
  // Data props
  myHand: PropTypes.array,
  declarations: PropTypes.object,
  players: PropTypes.array,
  currentTotal: PropTypes.number,

  // State props
  isMyTurn: PropTypes.bool,
  validOptions: PropTypes.array,
  declarationProgress: PropTypes.shape({
    declared: PropTypes.number,
    total: PropTypes.number,
  }),
  isLastPlayer: PropTypes.bool,
  estimatedPiles: PropTypes.number,
  handStrength: PropTypes.number,
  currentPlayer: PropTypes.string,
  myName: PropTypes.string,
  consecutiveZeros: PropTypes.number,
  redealMultiplier: PropTypes.number,

  // Action props
  onDeclare: PropTypes.func,
};

export default DeclarationUI;
