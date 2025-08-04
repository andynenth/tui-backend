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
    padding: spacing.xl,
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
    backgroundColor: colors.primary,
  },
  
  confettiColor2: {
    backgroundColor: colors.success,
  },
  
  confettiColor3: {
    backgroundColor: colors.warning,
  },
  
  confettiColor4: {
    backgroundColor: colors.danger,
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
    marginBottom: spacing.xl,
    animation: `${slideInUp} 0.5s ${motion.easeOut}`,
  },
  
  trophy: {
    fontSize: '5rem',
    animation: `${trophyBounce} 2s ${motion.easeInOut} infinite`,
  },
  
  winnerSection: {
    textAlign: 'center',
    marginBottom: spacing.xxl,
    animation: `${slideInUp} 0.5s ${motion.easeOut} 0.2s`,
    animationFillMode: 'both',
  },
  
  winnerName: {
    fontSize: typography.text3xl,
    fontWeight: typography.weightBold,
    background: gradients.gold,
    backgroundClip: 'text',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    marginBottom: spacing.sm,
  },
  
  winnerSubtitle: {
    fontSize: typography.textXl,
    color: colors.gray600,
    fontWeight: typography.weightMedium,
  },
  
  rankingsContainer: {
    width: '100%',
    maxWidth: '500px',
    marginBottom: spacing.xxl,
    animation: `${slideInUp} 0.5s ${motion.easeOut} 0.4s`,
    animationFillMode: 'both',
  },
  
  rankings: {
    backgroundColor: colors.white,
    borderRadius: layout.radiusXl,
    padding: spacing.lg,
    boxShadow: shadows.xl,
  },
  
  rankItem: {
    display: 'flex',
    alignItems: 'center',
    padding: spacing.md,
    borderBottom: `1px solid ${colors.gray200}`,
    
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
    borderRadius: layout.radiusFull,
    backgroundColor: colors.gray100,
    fontSize: typography.textBase,
    fontWeight: typography.weightBold,
    color: colors.gray700,
    marginRight: spacing.sm,
  },
  
  medal: {
    fontSize: '24px',
    marginRight: spacing.sm,
  },
  
  playerInfo: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.xxs,
  },
  
  playerName: {
    fontSize: typography.textBase,
    fontWeight: typography.weightMedium,
    color: colors.gray800,
  },
  
  playerScore: {
    fontSize: typography.textSm,
    color: colors.gray500,
  },
  
  finalScore: {
    fontSize: typography.textXl,
    fontWeight: typography.weightBold,
    color: colors.gray800,
  },
  
  stats: {
    backgroundColor: colors.gray50,
    borderRadius: layout.radiusLg,
    padding: spacing.lg,
    marginBottom: spacing.xl,
    width: '100%',
    maxWidth: '400px',
    animation: `${slideInUp} 0.5s ${motion.easeOut} 0.6s`,
    animationFillMode: 'both',
  },
  
  statsTitle: {
    fontSize: typography.textLg,
    fontWeight: typography.weightBold,
    color: colors.gray700,
    marginBottom: spacing.md,
    textAlign: 'center',
  },
  
  statItem: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: spacing.sm,
    borderBottom: `1px solid ${colors.gray200}`,
    
    ':last-child': {
      borderBottom: 'none',
    },
  },
  
  statLabel: {
    fontSize: typography.textSm,
    color: colors.gray600,
  },
  
  statValue: {
    fontSize: typography.textSm,
    fontWeight: typography.weightMedium,
    color: colors.gray800,
  },
  
  actions: {
    display: 'flex',
    gap: spacing.md,
    marginBottom: spacing.xl,
    animation: `${slideInUp} 0.5s ${motion.easeOut} 0.8s`,
    animationFillMode: 'both',
  },
  
  actionButton: {
    padding: `${spacing.md} ${spacing.xl}`,
    borderRadius: layout.radiusMd,
    fontSize: typography.textBase,
    fontWeight: typography.weightMedium,
    border: 'none',
    cursor: 'pointer',
    transition: `all ${motion.durationBase} ${motion.easeInOut}`,
  },
  
  primaryButton: {
    background: gradients.primary,
    color: colors.white,
    
    ':hover': {
      transform: 'translateY(-2px)',
      boxShadow: shadows.md,
    },
  },
  
  secondaryButton: {
    backgroundColor: colors.gray200,
    color: colors.gray600,
    
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
                      ? `${player.perfect_rounds} perfect round${player.perfect_rounds > 1 ? 's' : ''}`
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