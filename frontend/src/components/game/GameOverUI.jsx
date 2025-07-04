// frontend/src/components/game/GameOverUI.jsx

import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import Button from '../Button';

function GameOverUI({ finalRankings, gameStats, onBackToLobby }) {
  const [countdown, setCountdown] = useState(15); // 15-second countdown
  
  // Countdown timer effect
  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          // Auto-navigate to lobby
          if (onBackToLobby) {
            onBackToLobby();
          }
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    
    return () => clearInterval(timer);
  }, [onBackToLobby]);
  
  // Get ordinal suffix for rank
  const getOrdinalSuffix = (rank) => {
    const j = rank % 10;
    const k = rank % 100;
    if (j === 1 && k !== 11) return `${rank}st`;
    if (j === 2 && k !== 12) return `${rank}nd`;
    if (j === 3 && k !== 13) return `${rank}rd`;
    return `${rank}th`;
  };
  
  // Get rank styling class
  const getRankClass = (rank) => {
    switch(rank) {
      case 1: return 'bg-gradient-to-br from-yellow-400 to-orange-400 text-white shadow-lg shadow-yellow-500/30';
      case 2: return 'bg-gradient-to-br from-gray-300 to-gray-400 text-white shadow-lg shadow-gray-400/30';
      case 3: return 'bg-gradient-to-br from-orange-600 to-yellow-700 text-white shadow-lg shadow-orange-600/30';
      default: return 'bg-gradient-to-br from-gray-100 to-gray-200 text-gray-800 border-2 border-gray-300';
    }
  };
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 via-purple-700 to-purple-900 flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl shadow-2xl p-8 sm:p-10 max-w-2xl w-full animate-slideIn">
        {/* Celebration Emoji */}
        <div className="text-6xl mb-5 animate-pulse text-center">🎉</div>
        
        {/* Title */}
        <h1 className="text-4xl sm:text-5xl font-bold text-center mb-3 bg-gradient-to-r from-yellow-400 to-orange-400 bg-clip-text text-transparent">
          🏆 GAME COMPLETE 🏆
        </h1>
        <p className="text-xl text-gray-600 text-center mb-10">Congratulations to all players!</p>
        
        {/* Final Rankings */}
        <div className="mb-10">
          <h2 className="text-2xl font-bold text-gray-800 text-center mb-6">Final Rankings</h2>
          
          <div className="space-y-3">
            {finalRankings.map((player) => (
              <div
                key={player.name}
                className={`flex items-center justify-between p-4 rounded-xl transition-transform hover:translate-x-1 ${getRankClass(player.rank)}`}
              >
                <div className="flex items-center gap-4">
                  <span className="text-2xl font-bold min-w-[60px]">
                    {getOrdinalSuffix(player.rank)}
                  </span>
                  <span className="font-semibold text-lg">{player.name}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-bold text-xl">{player.score} points</span>
                  {player.rank === 1 && <span className="text-2xl animate-bounce">👑</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
        
        {/* Game Statistics */}
        <div className="bg-gray-50 rounded-2xl p-6 mb-10 border-2 border-gray-200">
          <h3 className="text-xl font-bold text-gray-800 mb-5 text-center">📊 Game Statistics</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="flex justify-between items-center p-3 bg-white rounded-lg shadow-sm">
              <span className="text-gray-600 font-medium">Total Rounds</span>
              <span className="text-gray-800 font-bold text-lg">{gameStats.total_rounds}</span>
            </div>
            <div className="flex justify-between items-center p-3 bg-white rounded-lg shadow-sm">
              <span className="text-gray-600 font-medium">Game Duration</span>
              <span className="text-gray-800 font-bold text-lg">{gameStats.game_duration}</span>
            </div>
          </div>
        </div>
        
        {/* Navigation */}
        <div className="text-center space-y-4">
          <Button
            onClick={onBackToLobby}
            variant="primary"
            size="large"
            className="px-10 py-3 text-lg font-semibold bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 transform hover:-translate-y-0.5 transition-all duration-200 shadow-lg hover:shadow-xl"
          >
            🏠 Back to Lobby
          </Button>
          
          {/* Countdown Display */}
          <p className="text-gray-500 text-sm">
            Auto-redirect in {countdown} second{countdown !== 1 ? 's' : ''}...
          </p>
        </div>
      </div>
    </div>
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