/**
 * 🏆 **ScoringUI Component** - Pure Scoring Phase Interface
 *
 * Phase 2, Task 2.2: Pure UI Components
 *
 * Features:
 * ✅ Pure functional component (props in, JSX out)
 * ✅ No hooks except local UI state
 * ✅ Comprehensive prop interfaces
 * ✅ Accessible and semantic HTML
 * ✅ Migrated to StyleX
 */

import React from 'react';
import PropTypes from 'prop-types';
import ScoringContent from './content/ScoringContent';

/**
 * Pure UI component for scoring phase
 * This component primarily handles data transformation and doesn't have its own styles
 */
export function ScoringUI({
  // Data props (all calculated by backend)
  players = [],
  roundScores = {},
  totalScores = {},
  redealMultiplier = 1,
  playersWithScores = [], // backend provides sorted players with all calculated data
  roundNumber = 1,
  playerName = '',

  // State props
  gameOver = false,
  winners = [],

  // Action props
  onStartNextRound,
}) {
  // Transform data for ScoringContent
  // Use backend-provided data or build from individual props
  const scores =
    playersWithScores.length > 0
      ? playersWithScores.map((player) => ({
          playerName: player.name,
          declared: player.pile_count || 0,
          actual: player.actualPiles || 0,
          hit: player.pile_count === player.actualPiles,
          hitValue:
            player.hitValue ||
            (player.pile_count === player.actualPiles
              ? player.pile_count
              : -Math.abs(player.pile_count - player.actualPiles)),
          bonus: player.bonus || 0,
          multiplier: redealMultiplier,
          roundScore: player.roundScore || roundScores[player.name] || 0,
          totalScore: player.totalScore || totalScores[player.name] || 0,
        }))
      : players.map((player) => ({
          playerName: player.name,
          declared: player.pile_count || 0,
          actual: player.actualPiles || 0,
          hit: player.pile_count === player.actualPiles,
          hitValue:
            player.pile_count === player.actualPiles
              ? player.pile_count
              : -Math.abs(player.pile_count - player.actualPiles),
          bonus:
            player.pile_count === player.actualPiles
              ? player.pile_count === 0
                ? 3
                : 5
              : 0,
          multiplier: redealMultiplier,
          roundScore: roundScores[player.name] || 0,
          totalScore: totalScores[player.name] || 0,
        }));

  return (
    <ScoringContent
      players={players}
      scores={scores}
      roundNumber={roundNumber}
      redealMultiplier={redealMultiplier}
      myName={playerName}
      onContinue={onStartNextRound}
    />
  );
}

// No helper functions needed - all calculations done by backend

// PropTypes definition
ScoringUI.propTypes = {
  // Data props (all calculated by backend)
  players: PropTypes.arrayOf(
    PropTypes.shape({
      name: PropTypes.string.isRequired,
      pile_count: PropTypes.number,
      actualPiles: PropTypes.number,
    })
  ).isRequired,
  roundScores: PropTypes.objectOf(PropTypes.number),
  totalScores: PropTypes.objectOf(PropTypes.number),
  redealMultiplier: PropTypes.number,
  roundNumber: PropTypes.number,
  playerName: PropTypes.string,
  playersWithScores: PropTypes.arrayOf(
    PropTypes.shape({
      name: PropTypes.string.isRequired,
      pile_count: PropTypes.number,
      actualPiles: PropTypes.number,
      roundScore: PropTypes.number,
      totalScore: PropTypes.number,
      baseScore: PropTypes.number,
      scoreExplanation: PropTypes.string,
      isWinner: PropTypes.bool,
    })
  ),

  // State props
  gameOver: PropTypes.bool,
  winners: PropTypes.arrayOf(PropTypes.string),

  // Action props
  onStartNextRound: PropTypes.func,
};

ScoringUI.defaultProps = {
  players: [],
  roundScores: {},
  totalScores: {},
  redealMultiplier: 1,
  roundNumber: 1,
  playerName: '',
  playersWithScores: [],
  gameOver: false,
  winners: [],
  onStartNextRound: null,
};

export default ScoringUI;