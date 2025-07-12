import React, { useCallback } from 'react';
import PropTypes from 'prop-types';
import { FooterTimer } from '../shared';
import '../../../styles/components/game/gameover.css';

const GameOverContent = ({ winner, finalScores, players, gameStats, onBackToLobby }) => {
  
  // Create confetti particles
  const createConfetti = () => {
    const particles = [];
    const colors = ['color-1', 'color-2', 'color-3', 'color-4', 'color-5', 'color-6'];
    const sizes = ['size-small', 'size-medium', 'size-large'];
    
    for (let i = 0; i < 50; i++) {
      const color = colors[Math.floor(Math.random() * colors.length)];
      const size = sizes[Math.floor(Math.random() * sizes.length)];
      const left = Math.random() * 100;
      const delay = Math.random() * 3;
      const duration = 3 + Math.random() * 2;
      
      particles.push(
        <div
          key={i}
          className={`go-confetti ${color} ${size}`}
          style={{
            left: `${left}%`,
            top: '-20px',
            animationDelay: `${delay}s`,
            animationDuration: `${duration}s`
          }}
        />
      );
    }
    
    return particles;
  };
  
  // Sort players by final score
  const sortedPlayers = [...players].sort((a, b) => {
    const scoreA = finalScores[a.id] || 0;
    const scoreB = finalScores[b.id] || 0;
    return scoreB - scoreA;
  });
  
  // Get medal for position
  const getMedal = (position) => {
    switch (position) {
      case 1: return '🥇';
      case 2: return '🥈';
      case 3: return '🥉';
      default: return null;
    }
  };
  
  // Handle return to lobby
  const handleReturnToLobby = useCallback(() => {
    if (onBackToLobby) {
      onBackToLobby();
    }
  }, [onBackToLobby]);
  
  // Format game duration
  const formatDuration = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    return `${minutes}`;
  };
  
  return (
    <div className="go-content">
      {/* Confetti animation */}
      <div className="go-confetti-container">
        {createConfetti()}
      </div>
      
      {/* Trophy */}
      <div className="go-trophy-container">
        <div className="go-trophy">🏆</div>
      </div>
      
      {/* Winner announcement */}
      <div className="go-winner-section">
        <div className="go-winner-name">{winner?.name || 'Unknown'}</div>
        <div className="go-winner-subtitle">Champion!</div>
      </div>
      
      {/* Final rankings */}
      <div className="go-rankings-container">
        <div className="go-rankings">
          {sortedPlayers.map((player, index) => {
            const position = index + 1;
            const medal = getMedal(position);
            const score = finalScores[player.id] || 0;
            
            return (
              <div key={player.id} className="go-rank-item">
                <div className="go-rank-position">{position}</div>
                {medal && <div className="go-medal">{medal}</div>}
                <div className="go-player-info">
                  <div className="go-player-name">{player.name}</div>
                  <div className="go-player-score">
                    {player.perfect_rounds > 0 
                      ? `${player.perfect_rounds} perfect round${player.perfect_rounds > 1 ? 's' : ''}` 
                      : 'Aim needs work 🎯'}
                  </div>
                </div>
                <div className="go-final-score">{score}</div>
              </div>
            );
          })}
        </div>
      </div>
      
      {/* Game statistics */}
      {gameStats && (
        <div className="go-stats">
          <div className="go-stats-title">Game Statistics</div>
          {gameStats.duration !== undefined && (
            <div className="go-stat-item">
              <span className="go-stat-label">Game Duration</span>
              <span className="go-stat-value">{formatDuration(gameStats.duration)}</span>
            </div>
          )}
          {gameStats.totalRounds && (
            <div className="go-stat-item">
              <span className="go-stat-label">Rounds Played</span>
              <span className="go-stat-value">{gameStats.totalRounds}</span>
            </div>
          )}
          {gameStats.highestScore !== undefined && (
            <div className="go-stat-item">
              <span className="go-stat-label">Highest Score</span>
              <span className="go-stat-value">{gameStats.highestScore}</span>
            </div>
          )}
        </div>
      )}
      
      {/* Action buttons */}
      <div className="go-actions">
        <button 
          className="go-action-button primary"
          onClick={handleReturnToLobby}
        >
          Return to Lobby
        </button>
        <button className="go-action-button secondary" disabled>
          Play Again
        </button>
      </div>
      
      {/* Countdown */}
      <FooterTimer
        duration={10}
        prefix="Returning to lobby in"
        suffix="seconds..."
        onComplete={handleReturnToLobby}
        variant="footer"
      />
    </div>
  );
};

GameOverContent.propTypes = {
  winner: PropTypes.shape({
    id: PropTypes.string,
    name: PropTypes.string
  }),
  finalScores: PropTypes.object.isRequired,
  players: PropTypes.array.isRequired,
  gameStats: PropTypes.shape({
    duration: PropTypes.number,
    totalRounds: PropTypes.number,
    highestScore: PropTypes.number
  }),
  onBackToLobby: PropTypes.func
};

export default GameOverContent;