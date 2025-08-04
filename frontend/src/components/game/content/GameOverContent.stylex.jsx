import React, { useCallback } from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, motion, layout, shadows, gradients } from '../../../design-system/tokens.stylex';
import { FooterTimer } from '../shared';

// Animations
const confettiFall = stylex.keyframes({
  '0%': {
    transform: 'translateY(0) rotate(0deg)',
    opacity: 1,
  },
  '100%': {
    transform: 'translateY(100vh) rotate(720deg)',
    opacity: 0,
  },
});

const trophyBounce = stylex.keyframes({
  '0%, 100%': {
    transform: 'scale(1) rotate(0deg)',
  },
  '25%': {
    transform: 'scale(1.1) rotate(-5deg)',
  },
  '75%': {
    transform: 'scale(1.1) rotate(5deg)',
  },
});

const slideInUp = stylex.keyframes({
  '0%': {
    opacity: 0,
    transform: 'translateY(30px)',
  },
  '100%': {
    opacity: 1,
    transform: 'translateY(0)',
  },
});

// GameOverContent styles
const styles = stylex.create({
  content: {
    position: 'relative',
    padding: '2rem',
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  },
  
  confettiContainer: {
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    pointerEvents: 'none',
    overflow: 'hidden',
  },
  
  confetti: {
    position: 'absolute',
    width: '10px',
    height: '10px',
    borderRadius: layout.radiusXs,
    animation: `${confettiFall} linear infinite`,
  },
  
  confettiColor1: {
    backgroundColor: '#0d6efd',
  },
  
  confettiColor2: {
    backgroundColor: '#198754',
  },
  
  confettiColor3: {
    backgroundColor: '#ffc107',
  },
  
  confettiColor4: {
    backgroundColor: '#dc3545',
  },
  
  confettiColor5: {
    backgroundColor: colors.purple,
  },
  
  confettiColor6: {
    backgroundColor: colors.pink,
  },
  
  confettiSmall: {
    width: '6px',
    height: '6px',
  },
  
  confettiMedium: {
    width: '8px',
    height: '8px',
  },
  
  confettiLarge: {
    width: '12px',
    height: '12px',
  },
  
  trophyContainer: {
    marginBottom: '2rem',
    animation: `${slideInUp} 0.5s 'cubic-bezier(0, 0, 0.2, 1)'`,
  },
  
  trophy: {
    fontSize: '5rem',
    animation: `${trophyBounce} 2s 'cubic-bezier(0.4, 0, 0.2, 1)' infinite`,
  },
  
  winnerSection: {
    textAlign: 'center',
    marginBottom: '3rem',
    animation: `${slideInUp} 0.5s 'cubic-bezier(0, 0, 0.2, 1)' 0.2s`,
    animationFillMode: 'both',
  },
  
  winnerName: {
    fontSize: '1.875rem',
    fontWeight: '700',
    background: gradients.gold,
    backgroundClip: 'text',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    marginBottom: '0.5rem',
  },
  
  winnerSubtitle: {
    fontSize: '1.25rem',
    color: '#6c757d',
    fontWeight: '500',
  },
  
  rankingsContainer: {
    width: '100%',
    maxWidth: '500px',
    marginBottom: '3rem',
    animation: `${slideInUp} 0.5s 'cubic-bezier(0, 0, 0.2, 1)' 0.4s`,
    animationFillMode: 'both',
  },
  
  rankings: {
    backgroundColor: '#ffffff',
    borderRadius: '1rem',
    padding: '1.5rem',
    boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  },
  
  rankItem: {
    display: 'flex',
    alignItems: 'center',
    padding: '1rem',
    borderBottomWidth: '1px',
    borderBottomStyle: 'solid',
    borderBottomColor: '#e9ecef',
    
    ':last-child': {
      borderBottom: 'none',
    },
  },
  
  rankPosition: {
    width: '32px',
    height: '32px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: '9999px',
    backgroundColor: '#f1f3f5',
    fontSize: '1rem',
    fontWeight: '700',
    color: '#495057',
    marginRight: '0.5rem',
  },
  
  medal: {
    fontSize: '24px',
    marginRight: '0.5rem',
  },
  
  playerInfo: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.xxs,
  },
  
  playerName: {
    fontSize: '1rem',
    fontWeight: '500',
    color: '#343a40',
  },
  
  playerScore: {
    fontSize: '0.875rem',
    color: '#adb5bd',
  },
  
  finalScore: {
    fontSize: '1.25rem',
    fontWeight: '700',
    color: '#343a40',
  },
  
  stats: {
    backgroundColor: '#f8f9fa',
    borderRadius: '0.5rem',
    padding: '1.5rem',
    marginBottom: '2rem',
    width: '100%',
    maxWidth: '400px',
    animation: `${slideInUp} 0.5s 'cubic-bezier(0, 0, 0.2, 1)' 0.6s`,
    animationFillMode: 'both',
  },
  
  statsTitle: {
    fontSize: '1.125rem',
    fontWeight: '700',
    color: '#495057',
    marginBottom: '1rem',
    textAlign: 'center',
  },
  
  statItem: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '0.5rem',
    borderBottomWidth: '1px',
    borderBottomStyle: 'solid',
    borderBottomColor: '#e9ecef',
    
    ':last-child': {
      borderBottom: 'none',
    },
  },
  
  statLabel: {
    fontSize: '0.875rem',
    color: '#6c757d',
  },
  
  statValue: {
    fontSize: '0.875rem',
    fontWeight: '500',
    color: '#343a40',
  },
  
  actions: {
    display: 'flex',
    gap: '1rem',
    marginBottom: '2rem',
    animation: `${slideInUp} 0.5s 'cubic-bezier(0, 0, 0.2, 1)' 0.8s`,
    animationFillMode: 'both',
  },
  
  actionButton: {
    padding: `'1rem' '2rem'`,
    borderRadius: '0.375rem',
    fontSize: '1rem',
    fontWeight: '500',
    border: 'none',
    cursor: 'pointer',
    transition: `all '300ms' 'cubic-bezier(0.4, 0, 0.2, 1)'`,
  },
  
  primaryButton: {
    background: gradients.primary,
    color: '#ffffff',
    
    ':hover': {
      transform: 'translateY(-2px)',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    },
  },
  
  secondaryButton: {
    backgroundColor: '#e9ecef',
    color: '#6c757d',
    
    ':disabled': {
      opacity: 0.5,
      cursor: 'not-allowed',
    },
  },
});

const GameOverContent = ({
  winner,
  finalScores,
  players,
  gameStats,
  onBackToLobby,
}) => {
  // Create confetti particles
  const createConfetti = () => {
    const particles = [];
    const colorStyles = [
      styles.confettiColor1,
      styles.confettiColor2,
      styles.confettiColor3,
      styles.confettiColor4,
      styles.confettiColor5,
      styles.confettiColor6,
    ];
    const sizeStyles = [
      styles.confettiSmall,
      styles.confettiMedium,
      styles.confettiLarge,
    ];

    for (let i = 0; i < 50; i++) {
      const colorStyle = colorStyles[Math.floor(Math.random() * colorStyles.length)];
      const sizeStyle = sizeStyles[Math.floor(Math.random() * sizeStyles.length)];
      const left = Math.random() * 100;
      const delay = Math.random() * 3;
      const duration = 3 + Math.random() * 2;

      particles.push(
        <div
          key={i}
          {...stylex.props(
            styles.confetti,
            colorStyle,
            sizeStyle
          )}
          style={{
            left: `${left}%`,
            top: '-20px',
            animationDelay: `${delay}s`,
            animationDuration: `${duration}s`,
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
      case 1:
        return '🥇';
      case 2:
        return '🥈';
      case 3:
        return '🥉';
      default:
        return null;
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
    return `${minutes} min`;
  };

  return (
    <div {...stylex.props(styles.content)}>
      {/* Confetti animation */}
      <div {...stylex.props(styles.confettiContainer)}>
        {createConfetti()}
      </div>

      {/* Trophy */}
      <div {...stylex.props(styles.trophyContainer)}>
        <div {...stylex.props(styles.trophy)}>🏆</div>
      </div>

      {/* Winner announcement */}
      <div {...stylex.props(styles.winnerSection)}>
        <div {...stylex.props(styles.winnerName)}>
          {winner?.name || 'Unknown'}
        </div>
        <div {...stylex.props(styles.winnerSubtitle)}>
          Champion!
        </div>
      </div>

      {/* Final rankings */}
      <div {...stylex.props(styles.rankingsContainer)}>
        <div {...stylex.props(styles.rankings)}>
          {sortedPlayers.map((player, index) => {
            const position = index + 1;
            const medal = getMedal(position);
            const score = finalScores[player.id] || 0;

            return (
              <div key={player.id} {...stylex.props(styles.rankItem)}>
                <div {...stylex.props(styles.rankPosition)}>
                  {position}
                </div>
                {medal && (
                  <div {...stylex.props(styles.medal)}>{medal}</div>
                )}
                <div {...stylex.props(styles.playerInfo)}>
                  <div {...stylex.props(styles.playerName)}>
                    {player.name}
                  </div>
                  <div {...stylex.props(styles.playerScore)}>
                    {player.perfect_rounds > 0
                      ? `${player.perfect_rounds} perfect round${player.perfect_rounds > 1 ? 's' : '}`
                      : 'Aim needs work 🎯'}
                  </div>
                </div>
                <div {...stylex.props(styles.finalScore)}>
                  {score}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Game statistics */}
      {gameStats && (
        <div {...stylex.props(styles.stats)}>
          <div {...stylex.props(styles.statsTitle)}>
            Game Statistics
          </div>
          {gameStats.duration !== undefined && (
            <div {...stylex.props(styles.statItem)}>
              <span {...stylex.props(styles.statLabel)}>
                Game Duration
              </span>
              <span {...stylex.props(styles.statValue)}>
                {formatDuration(gameStats.duration)}
              </span>
            </div>
          )}
          {gameStats.totalRounds && (
            <div {...stylex.props(styles.statItem)}>
              <span {...stylex.props(styles.statLabel)}>
                Rounds Played
              </span>
              <span {...stylex.props(styles.statValue)}>
                {gameStats.totalRounds}
              </span>
            </div>
          )}
          {gameStats.highestScore !== undefined && (
            <div {...stylex.props(styles.statItem)}>
              <span {...stylex.props(styles.statLabel)}>
                Highest Score
              </span>
              <span {...stylex.props(styles.statValue)}>
                {gameStats.highestScore}
              </span>
            </div>
          )}
        </div>
      )}

      {/* Action buttons */}
      <div {...stylex.props(styles.actions)}>
        <button
          {...stylex.props(styles.actionButton, styles.primaryButton)}
          onClick={handleReturnToLobby}
        >
          Return to Lobby
        </button>
        <button 
          {...stylex.props(styles.actionButton, styles.secondaryButton)}
          disabled
        >
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
    name: PropTypes.string,
  }),
  finalScores: PropTypes.object.isRequired,
  players: PropTypes.array.isRequired,
  gameStats: PropTypes.shape({
    duration: PropTypes.number,
    totalRounds: PropTypes.number,
    highestScore: PropTypes.number,
  }),
  onBackToLobby: PropTypes.func,
};

export default GameOverContent;