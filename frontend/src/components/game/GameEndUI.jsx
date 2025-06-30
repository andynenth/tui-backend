// frontend/src/components/game/GameEndUI.jsx

import React from 'react';
import { useGameActions } from '../../hooks/useGameActions';

const GameEndUI = ({ gameState }) => {
  const gameActions = useGameActions();

  // Create sorted rankings from gameState data
  const createFinalRankings = () => {
    if (!gameState?.players) return [];
    
    // Sort players by score (highest first)
    const sortedPlayers = [...gameState.players].sort((a, b) => b.score - a.score);
    
    // Assign ranks (handle ties)
    const rankings = [];
    let currentRank = 1;
    
    for (let i = 0; i < sortedPlayers.length; i++) {
      const player = sortedPlayers[i];
      
      // Check for ties with previous player
      if (i > 0 && player.score === sortedPlayers[i-1].score) {
        // Same score as previous player - same rank
        const rank = rankings[i-1].rank;
        rankings.push({
          rank,
          name: player.name,
          score: player.score,
          isWinner: rank === 1
        });
      } else {
        // Different score - new rank
        rankings.push({
          rank: currentRank,
          name: player.name,
          score: player.score,
          isWinner: currentRank === 1
        });
      }
      
      currentRank = i + 2; // Next unique rank position
    }
    
    return rankings;
  };

  const handleBackToLobby = async () => {
    try {
      console.log('🏠 GameEndUI: Back to Lobby clicked');
      
      // Send NAVIGATE_TO_LOBBY action to backend
      await gameActions.sendAction('navigate_to_lobby', {});
      
      // Navigate immediately on frontend (don't wait for backend response)
      window.location.href = '/lobby';
      
    } catch (error) {
      console.error('Error navigating to lobby:', error);
      // Fallback navigation even if action fails
      window.location.href = '/lobby';
    }
  };

  const finalRankings = createFinalRankings();
  const gameStats = gameState?.phase_data?.game_statistics || {};
  
  // Get winner text
  const winners = finalRankings.filter(player => player.isWinner);
  const winnerText = winners.length === 1 
    ? `Winner: ${winners[0].name}!`
    : winners.length > 1 
    ? `Winners: ${winners.map(w => w.name).join(', ')}!`
    : 'Game Complete!';

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 via-blue-600 to-indigo-700 flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl shadow-2xl p-8 max-w-2xl w-full mx-auto transform animate-fadeIn">
        
        {/* Celebration Header */}
        <div className="text-center mb-8">
          <div className="text-6xl mb-4 animate-bounce">🎉</div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-yellow-400 to-orange-500 bg-clip-text text-transparent mb-2">
            🏆 GAME COMPLETE 🏆
          </h1>
          <p className="text-xl text-gray-600">{winnerText}</p>
        </div>

        {/* Final Rankings */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-800 mb-6 text-center">Final Rankings</h2>
          
          <div className="space-y-3">
            {finalRankings.map((player, index) => (
              <div
                key={player.name}
                className={`
                  flex items-center justify-between p-4 rounded-xl font-semibold text-lg transition-all duration-200 hover:transform hover:translate-x-1
                  ${player.rank === 1 ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-white shadow-lg shadow-yellow-300/30' : ''}
                  ${player.rank === 2 ? 'bg-gradient-to-r from-gray-300 to-gray-400 text-white shadow-lg shadow-gray-300/30' : ''}
                  ${player.rank === 3 ? 'bg-gradient-to-r from-amber-600 to-yellow-700 text-white shadow-lg shadow-amber-300/30' : ''}
                  ${player.rank >= 4 ? 'bg-gradient-to-r from-gray-100 to-gray-200 text-gray-800 border-2 border-gray-300' : ''}
                `}
              >
                <div className="flex items-center space-x-4">
                  <span className="text-2xl font-bold min-w-[3rem]">
                    {player.rank === 1 ? '1st' : player.rank === 2 ? '2nd' : player.rank === 3 ? '3rd' : `${player.rank}th`}
                  </span>
                  <span className="text-xl">{player.name}</span>
                </div>
                
                <div className="flex items-center space-x-2">
                  <span className="text-xl font-bold">{player.score} points</span>
                  {player.isWinner && (
                    <span className="text-2xl animate-pulse">👑</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Game Statistics */}
        <div className="bg-gray-50 rounded-2xl p-6 mb-8 border-2 border-gray-200">
          <h3 className="text-xl font-bold text-gray-800 mb-4 text-center">📊 Game Statistics</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white rounded-lg p-4 shadow-sm">
              <div className="flex justify-between items-center">
                <span className="text-gray-600 font-medium">Total Rounds</span>
                <span className="text-gray-900 font-bold text-lg">
                  {gameStats.total_rounds || gameState?.round_number || '?'}
                </span>
              </div>
            </div>
            
            <div className="bg-white rounded-lg p-4 shadow-sm">
              <div className="flex justify-between items-center">
                <span className="text-gray-600 font-medium">Game Duration</span>
                <span className="text-gray-900 font-bold text-lg">
                  {gameStats.game_duration || 'Unknown'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Back to Lobby Button */}
        <div className="text-center">
          <button
            onClick={handleBackToLobby}
            className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-bold py-4 px-8 rounded-full text-lg shadow-lg shadow-purple-300/30 transition-all duration-300 hover:transform hover:-translate-y-1 hover:shadow-xl focus:outline-none focus:ring-4 focus:ring-purple-300"
          >
            🏠 Back to Lobby
          </button>
        </div>
      </div>
    </div>
  );
};

export default GameEndUI;