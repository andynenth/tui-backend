// frontend/src/components/game/GameOverUI.jsx

import React from 'react';
import PropTypes from 'prop-types';
import GameOverContent from './content/GameOverContent';

function GameOverUI({ finalRankings, gameStats, onBackToLobby }) {
  // Transform data for GameOverContent
  const players = finalRankings.map(ranking => ({
    id: ranking.name, // Using name as ID for now
    name: ranking.name,
    turns_won: ranking.turns_won || 0,
    perfect_rounds: ranking.perfect_rounds || 0
  }));
  
  const finalScores = finalRankings.reduce((acc, ranking) => {
    acc[ranking.name] = ranking.score;
    return acc;
  }, {});
  
  const winner = finalRankings.find(ranking => ranking.rank === 1);
  const winnerData = winner ? { id: winner.name, name: winner.name } : null;
  
  // Transform game stats
  const transformedStats = {
    totalRounds: gameStats.total_rounds,
    duration: gameStats.game_duration ? parseGameDuration(gameStats.game_duration) : undefined,
    highestScore: finalRankings.length > 0 ? Math.max(...finalRankings.map(r => r.score)) : 0
  };
  
  // Helper to parse duration string "45 min" to seconds
  function parseGameDuration(durationStr) {
    const match = durationStr.match(/(\d+)\s*min/);
    if (match) {
      return parseInt(match[1]) * 60; // Convert minutes to seconds
    }
    return 0;
  }
  
  return (
    <GameOverContent
      winner={winnerData}
      finalScores={finalScores}
      players={players}
      gameStats={transformedStats}
      onBackToLobby={onBackToLobby}
    />
  );
}

// Animation keyframes for Tailwind (add to tailwind.config.js)
// @keyframes slideIn {
//   from {
//     opacity: 0;
//     transform: translateY(-50px);
//   }
//   to {
//     opacity: 1;
//     transform: translateY(0);
//   }
// }

GameOverUI.propTypes = {
  finalRankings: PropTypes.arrayOf(PropTypes.shape({
    name: PropTypes.string.isRequired,
    score: PropTypes.number.isRequired,
    rank: PropTypes.number.isRequired
  })).isRequired,
  gameStats: PropTypes.shape({
    total_rounds: PropTypes.number.isRequired,
    game_duration: PropTypes.string.isRequired
  }).isRequired,
  winners: PropTypes.arrayOf(PropTypes.string),
  onBackToLobby: PropTypes.func.isRequired
};

GameOverUI.defaultProps = {
  winners: []
};

export default GameOverUI;