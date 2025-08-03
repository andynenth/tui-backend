/**
 * 🏆 **GameOverUI Component** - Game Over Phase Interface with StyleX
 *
 * Displays final game results with celebration animations
 *
 * Features:
 * ✅ Winner announcement with trophy
 * ✅ Final rankings with medals
 * ✅ Game statistics
 * ✅ Confetti animation
 * ✅ Return to lobby button
 */

import React, { useCallback } from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
import Button from '../Button.stylex';
import FooterTimer from './shared/FooterTimer.stylex';
import { colors, spacing, shadows, layout, motion, typography } from '../../design-system/tokens.stylex';

// Animation keyframes
const confettiFall = stylex.keyframes({
  '0%': {
    transform: 'translateY(-100vh) rotate(0deg)',
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

const slideIn = stylex.keyframes({
  '0%': {
    opacity: 0,
    transform: 'translateY(-50px)',
  },
  '100%': {
    opacity: 1,
    transform: 'translateY(0)',
  },
});

const shimmer = stylex.keyframes({
  '0%': {
    backgroundPosition: '-200% 0',
  },
  '100%': {
    backgroundPosition: '200% 0',
  },
});

const styles = stylex.create({
  container: {
    position: 'relative',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: spacing.xl,
    padding: spacing.xl,
    minHeight: '100%',
    overflow: 'hidden',
  },
  
  // Confetti styles
  confettiContainer: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    pointerEvents: 'none',
    overflow: 'hidden',
  },
  
  confetti: {
    position: 'absolute',
    width: '10px',
    height: '10px',
    animation: `${confettiFall} linear infinite`,
  },
  
  confettiColor1: {
    backgroundColor: colors.primary,
  },
  
  confettiColor2: {
    backgroundColor: colors.secondary,
  },
  
  confettiColor3: {
    backgroundColor: colors.success,
  },
  
  confettiColor4: {
    backgroundColor: colors.warning,
  },
  
  confettiColor5: {
    backgroundColor: colors.danger,
  },
  
  confettiColor6: {
    backgroundColor: colors.pieceGold,
  },
  
  confettiSizeSmall: {
    width: '6px',
    height: '6px',
  },
  
  confettiSizeMedium: {
    width: '10px',
    height: '10px',
  },
  
  confettiSizeLarge: {
    width: '14px',
    height: '14px',
  },
  
  // Trophy section
  trophyContainer: {
    animation: `${slideIn} ${motion.durationNormal} ${motion.easeOut}`,
    animationDelay: '0.2s',
    animationFillMode: 'both',
  },
  
  trophy: {
    fontSize: '6rem',
    animation: `${trophyBounce} 2s ${motion.easeInOut} infinite`,
    filter: 'drop-shadow(0 4px 8px rgba(0, 0, 0, 0.2))',
  },
  
  // Winner section
  winnerSection: {
    textAlign: 'center',
    animation: `${slideIn} ${motion.durationNormal} ${motion.easeOut}`,
    animationDelay: '0.4s',
    animationFillMode: 'both',
  },
  
  winnerName: {
    fontSize: typography.textXxxl,
    fontWeight: typography.weightBold,
    color: colors.textDark,
    marginBottom: spacing.sm,
    background: `linear-gradient(90deg, ${colors.primary}, ${colors.secondary}, ${colors.primary})`,
    backgroundSize: '200% auto',
    backgroundClip: 'text',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    animation: `${shimmer} 3s linear infinite`,
  },
  
  winnerSubtitle: {
    fontSize: typography.textXl,
    color: colors.gray600,
    fontStyle: 'italic',
  },
  
  // Rankings section
  rankingsSection: {
    width: '100%',
    maxWidth: '500px',
    animation: `${slideIn} ${motion.durationNormal} ${motion.easeOut}`,
    animationDelay: '0.6s',
    animationFillMode: 'both',
  },
  
  rankingsTitle: {
    fontSize: typography.textLg,
    fontWeight: typography.weightBold,
    color: colors.textDark,
    marginBottom: spacing.md,
    textAlign: 'center',
  },
  
  rankingsList: {
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.sm,
  },
  
  rankingItem: {
    display: 'flex',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderRadius: layout.radiusMd,
    padding: spacing.md,
    boxShadow: shadows.sm,
    transition: motion.transitionBase,
    
    ':hover': {
      transform: 'translateX(4px)',
      boxShadow: shadows.md,
    },
  },
  
  rankingPosition: {
    width: '40px',
    fontSize: typography.textXl,
    fontWeight: typography.weightBold,
    textAlign: 'center',
  },
  
  rankingPlayer: {
    flex: 1,
    marginLeft: spacing.md,
    fontSize: typography.textMd,
    fontWeight: typography.weightMedium,
    color: colors.textDark,
  },
  
  rankingScore: {
    fontSize: typography.textLg,
    fontWeight: typography.weightBold,
    color: colors.primary,
  },
  
  rankingStats: {
    marginLeft: spacing.md,
    fontSize: typography.textSm,
    color: colors.gray600,
    display: 'flex',
    gap: spacing.sm,
  },
  
  // Game stats section
  statsSection: {
    backgroundColor: colors.surface,
    borderRadius: layout.radiusMd,
    padding: spacing.lg,
    boxShadow: shadows.md,
    animation: `${slideIn} ${motion.durationNormal} ${motion.easeOut}`,
    animationDelay: '0.8s',
    animationFillMode: 'both',
  },
  
  statsTitle: {
    fontSize: typography.textMd,
    fontWeight: typography.weightBold,
    color: colors.gray700,
    marginBottom: spacing.sm,
    textAlign: 'center',
  },
  
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: spacing.md,
    textAlign: 'center',
  },
  
  statItem: {
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.xs,
  },
  
  statValue: {
    fontSize: typography.textXl,
    fontWeight: typography.weightBold,
    color: colors.primary,
  },
  
  statLabel: {
    fontSize: typography.textSm,
    color: colors.gray600,
  },
  
  // Actions section
  actionsSection: {
    marginTop: spacing.xl,
    animation: `${slideIn} ${motion.durationNormal} ${motion.easeOut}`,
    animationDelay: '1s',
    animationFillMode: 'both',
  },
  
  // Responsive
  '@media (max-width: 640px)': {
    trophy: {
      fontSize: '4rem',
    },
    
    winnerName: {
      fontSize: typography.textXxl,
    },
    
    statsGrid: {
      gridTemplateColumns: '1fr',
    },
  },
});

/**
 * Pure UI component for game over phase with integrated content
 */
export function GameOverUI({
  finalRankings,
  gameStats,
  onBackToLobby,
  className = '',
}) {
  // Transform data
  const players = finalRankings.map((ranking) => ({
    id: ranking.name,
    name: ranking.name,
    turns_won: ranking.turns_won || 0,
    perfect_rounds: ranking.perfect_rounds || 0,
  }));
  
  const finalScores = finalRankings.reduce((acc, ranking) => {
    acc[ranking.name] = ranking.score;
    return acc;
  }, {});
  
  const winner = finalRankings.find((ranking) => ranking.rank === 1);
  const winnerData = winner ? { id: winner.name, name: winner.name } : null;
  
  // Helper to parse duration string "45 min" to minutes
  function parseGameDuration(durationStr) {
    const match = durationStr.match(/(\d+)\s*min/);
    if (match) {
      return parseInt(match[1]);
    }
    return 0;
  }
  
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
  
  // Create confetti particles
  const createConfetti = () => {
    const particles = [];
    const colorClasses = [
      styles.confettiColor1,
      styles.confettiColor2,
      styles.confettiColor3,
      styles.confettiColor4,
      styles.confettiColor5,
      styles.confettiColor6,
    ];
    const sizeClasses = [
      styles.confettiSizeSmall,
      styles.confettiSizeMedium,
      styles.confettiSizeLarge,
    ];
    
    for (let i = 0; i < 50; i++) {
      const colorClass = colorClasses[Math.floor(Math.random() * colorClasses.length)];
      const sizeClass = sizeClasses[Math.floor(Math.random() * sizeClasses.length)];
      const left = Math.random() * 100;
      const delay = Math.random() * 3;
      const duration = 3 + Math.random() * 2;
      
      particles.push(
        <div
          key={i}
          {...stylex.props(styles.confetti, colorClass, sizeClass)}
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
  
  // Handle return to lobby
  const handleReturnToLobby = useCallback(() => {
    if (onBackToLobby) {
      onBackToLobby();
    }
  }, [onBackToLobby]);
  
  return (
    <div {...stylex.props(styles.container, className && { className })}>
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
          {winnerData?.name || 'Unknown'}
        </div>
        <div {...stylex.props(styles.winnerSubtitle)}>Champion!</div>
      </div>
      
      {/* Final rankings */}
      <div {...stylex.props(styles.rankingsSection)}>
        <h3 {...stylex.props(styles.rankingsTitle)}>Final Rankings</h3>
        <div {...stylex.props(styles.rankingsList)}>
          {sortedPlayers.map((player, index) => {
            const position = index + 1;
            const medal = getMedal(position);
            const score = finalScores[player.id] || 0;
            
            return (
              <div key={player.id} {...stylex.props(styles.rankingItem)}>
                <div {...stylex.props(styles.rankingPosition)}>
                  {medal || position}
                </div>
                <div {...stylex.props(styles.rankingPlayer)}>
                  {player.name}
                </div>
                <div {...stylex.props(styles.rankingScore)}>
                  {score} pts
                </div>
                <div {...stylex.props(styles.rankingStats)}>
                  <span>🎯 {player.turns_won}</span>
                  <span>⭐ {player.perfect_rounds}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
      
      {/* Game statistics */}
      <div {...stylex.props(styles.statsSection)}>
        <h3 {...stylex.props(styles.statsTitle)}>Game Statistics</h3>
        <div {...stylex.props(styles.statsGrid)}>
          <div {...stylex.props(styles.statItem)}>
            <div {...stylex.props(styles.statValue)}>
              {gameStats.total_rounds}
            </div>
            <div {...stylex.props(styles.statLabel)}>Rounds</div>
          </div>
          <div {...stylex.props(styles.statItem)}>
            <div {...stylex.props(styles.statValue)}>
              {parseGameDuration(gameStats.game_duration)} min
            </div>
            <div {...stylex.props(styles.statLabel)}>Duration</div>
          </div>
          <div {...stylex.props(styles.statItem)}>
            <div {...stylex.props(styles.statValue)}>
              {Math.max(...finalRankings.map((r) => r.score))}
            </div>
            <div {...stylex.props(styles.statLabel)}>High Score</div>
          </div>
        </div>
      </div>
      
      {/* Actions */}
      <div {...stylex.props(styles.actionsSection)}>
        <FooterTimer
          duration={30}
          prefix="Returning to lobby in"
          onComplete={handleReturnToLobby}
          variant="minimal"
        />
        <Button
          onClick={handleReturnToLobby}
          variant="primary"
          size="large"
        >
          Back to Lobby
        </Button>
      </div>
    </div>
  );
}

// PropTypes definition
GameOverUI.propTypes = {
  finalRankings: PropTypes.arrayOf(
    PropTypes.shape({
      name: PropTypes.string.isRequired,
      score: PropTypes.number.isRequired,
      rank: PropTypes.number.isRequired,
      turns_won: PropTypes.number,
      perfect_rounds: PropTypes.number,
    })
  ).isRequired,
  gameStats: PropTypes.shape({
    total_rounds: PropTypes.number.isRequired,
    game_duration: PropTypes.string.isRequired,
  }).isRequired,
  onBackToLobby: PropTypes.func.isRequired,
  className: PropTypes.string,
};

GameOverUI.defaultProps = {
  className: '',
};

export default GameOverUI;