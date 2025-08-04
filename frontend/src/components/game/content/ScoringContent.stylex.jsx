import React from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, motion, layout, shadows, gradients } from '../../../design-system/tokens.stylex';
import { PlayerAvatar, FooterTimer } from '../shared';

// Animations
const slideIn = stylex.keyframes({
  '0%': {
    opacity: 0,
    transform: 'translateY(20px)',
  },
  '100%': {
    opacity: 1,
    transform: 'translateY(0)',
  },
});

const shine = stylex.keyframes({
  '0%': {
    backgroundPosition: '-200% center',
  },
  '100%': {
    backgroundPosition: '200% center',
  },
});

// ScoringContent styles
const styles = stylex.create({
  scoringSection: {
    padding: spacing.lg,
    flex: 1,
    overflowY: 'auto',
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.md,
  },
  
  scoreCard: {
    backgroundColor: colors.white,
    borderRadius: layout.radiusLg,
    padding: spacing.lg,
    boxShadow: shadows.md,
    animation: `${slideIn} 0.3s ${motion.easeOut}`,
    animationFillMode: 'both',
  },
  
  topRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.md,
    paddingBottom: spacing.md,
    borderBottom: `1px solid ${colors.gray200}`,
  },
  
  playerInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.md,
  },
  
  playerName: {
    fontSize: typography.textLg,
    fontWeight: typography.weightMedium,
    color: colors.gray800,
  },
  
  totalScore: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'flex-end',
    gap: spacing.xxs,
  },
  
  totalLabel: {
    fontSize: typography.textSm,
    color: colors.gray500,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
  
  totalValue: {
    fontSize: typography.text2xl,
    fontWeight: typography.weightBold,
  },
  
  totalNeutral: {
    color: colors.gray700,
  },
  
  bottomRow: {
    display: 'flex',
    justifyContent: 'space-between',
    gap: spacing.md,
  },
  
  stat: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: spacing.xxs,
    flex: 1,
  },
  
  statTarget: {
    borderRight: `1px solid ${colors.gray200}`,
    paddingRight: spacing.md,
  },
  
  statLabel: {
    fontSize: typography.textXs,
    color: colors.gray500,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
  
  targetValue: {
    fontSize: typography.textLg,
    fontWeight: typography.weightBold,
  },
  
  statValue: {
    fontSize: typography.textBase,
    fontWeight: typography.weightMedium,
  },
  
  valuePositive: {
    color: colors.success,
  },
  
  valueNegative: {
    color: colors.danger,
  },
  
  valueNeutral: {
    color: colors.gray600,
  },
  
  valueBlue: {
    color: colors.primary,
  },
  
  multiplier: {
    fontSize: typography.textBase,
    fontWeight: typography.weightBold,
    color: colors.warning,
    padding: `${spacing.xxs} ${spacing.sm}`,
    backgroundColor: 'rgba(245, 158, 11, 0.1)',
    borderRadius: layout.radiusSm,
  },
  
  continueSection: {
    padding: spacing.lg,
    backgroundColor: colors.gray50,
    borderTop: `1px solid ${colors.gray200}`,
  },
  
  continueInfo: {
    textAlign: 'center',
  },
  
  nextRound: {
    fontSize: typography.textLg,
    fontWeight: typography.weightMedium,
    color: colors.gray700,
    marginBottom: spacing.md,
  },
  
  autoContinue: {
    display: 'flex',
    justifyContent: 'center',
  },
  
  perfectScore: {
    background: `linear-gradient(90deg, ${colors.success}33 0%, ${colors.success}66 50%, ${colors.success}33 100%)`,
    backgroundSize: '200% 100%',
    animation: `${shine} 3s linear infinite`,
  },
});

/**
 * ScoringContent Component
 *
 * Displays the scoring phase with:
 * - Player score cards with detailed scoring breakdown
 * - Declared vs actual piles
 * - Hit/penalty calculation
 * - Bonus points
 * - Multiplier display
 * - Total scores
 * - Auto-countdown timer
 */
const ScoringContent = ({
  players = [],
  scores = [], // Array of score objects
  roundNumber = 1,
  redealMultiplier = 1,
  myName = '',
  onContinue,
}) => {
  // Format score display
  const formatScore = (value) => {
    if (value > 0) return `+${value}`;
    return value.toString();
  };

  // Get target color style
  const getTargetStyle = (score) => {
    if (score.declared === 0 && score.actual === 0) return styles.valueBlue;
    if (score.declared === score.actual) return styles.valuePositive; // Green for hits
    return styles.valueNegative; // Red for misses
  };

  // Get result style - special handling for zero/zero
  const getResultStyle = (score) => {
    // Special case: 0/0 shows as blue
    if (score.declared === 0 && score.actual === 0) return styles.valueBlue;
    if (score.hit) return styles.valuePositive;
    return styles.valueNegative;
  };

  // Get bonus style - special handling for zero/zero
  const getBonusStyle = (score) => {
    // Special case: 0/0 bonus is blue
    if (score.declared === 0 && score.actual === 0) return styles.valueBlue;
    if (score.bonus > 0) return styles.valuePositive;
    return styles.valueNeutral;
  };

  // Get round score style - special handling for zero/zero
  const getRoundScoreStyle = (score) => {
    if (score.declared === 0 && score.actual === 0) return styles.valueBlue;
    if (score.roundScore > 0) return styles.valuePositive;
    if (score.roundScore < 0) return styles.valueNegative;
    return styles.valueNeutral;
  };

  return (
    <>
      {/* Scoring section */}
      <div {...stylex.props(styles.scoringSection)}>
        {scores.map((score, index) => {
          const player = players.find((p) => p.name === score.playerName) || {
            name: score.playerName,
          };

          // Debug logging
          console.log(
            '🎨 Scoring player data:',
            player.name,
            'avatar_color:',
            player.avatar_color,
            'is_bot:',
            player.is_bot,
            'full player:',
            player
          );

          const isPerfectScore = score.hit && score.declared > 0;

          return (
            <div 
              key={player.name} 
              {...stylex.props(
                styles.scoreCard,
                isPerfectScore && styles.perfectScore
              )}
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              {/* Top row - player and total */}
              <div {...stylex.props(styles.topRow)}>
                <div {...stylex.props(styles.playerInfo)}>
                  <PlayerAvatar
                    name={player.name}
                    isBot={player.is_bot}
                    avatarColor={player.avatar_color}
                    size="medium"
                  />
                  <div {...stylex.props(styles.playerName)}>
                    {player.name}
                    {player.name === myName ? ' (You)' : ''}
                  </div>
                </div>

                <div {...stylex.props(styles.totalScore)}>
                  <span {...stylex.props(styles.totalLabel)}>Total:</span>
                  <span {...stylex.props(styles.totalValue, styles.totalNeutral)}>
                    {score.totalScore}
                  </span>
                </div>
              </div>

              {/* Bottom row - scoring details */}
              <div {...stylex.props(styles.bottomRow)}>
                {/* Target */}
                <div {...stylex.props(styles.stat, styles.statTarget)}>
                  <span {...stylex.props(styles.statLabel)}>Target</span>
                  <span {...stylex.props(
                    styles.targetValue,
                    getTargetStyle(score)
                  )}>
                    {score.actual}/{score.declared}
                  </span>
                </div>

                {/* Hit/Penalty */}
                <div {...stylex.props(styles.stat)}>
                  <span {...stylex.props(styles.statLabel)}>
                    {score.hit ? 'Hit' : 'Penalty'}
                  </span>
                  <span {...stylex.props(
                    styles.statValue,
                    getResultStyle(score)
                  )}>
                    {formatScore(score.hitValue)}
                  </span>
                </div>

                {/* Bonus */}
                <div {...stylex.props(styles.stat)}>
                  <span {...stylex.props(styles.statLabel)}>Bonus</span>
                  <span {...stylex.props(
                    styles.statValue,
                    getBonusStyle(score)
                  )}>
                    {formatScore(score.bonus)}
                  </span>
                </div>

                {/* Multiplier if applicable */}
                {score.multiplier > 1 && (
                  <div {...stylex.props(styles.stat)}>
                    <span {...stylex.props(styles.statLabel)}>Mult</span>
                    <span {...stylex.props(styles.multiplier)}>
                      ×{score.multiplier}
                    </span>
                  </div>
                )}

                {/* Round score */}
                <div {...stylex.props(styles.stat)}>
                  <span {...stylex.props(styles.statLabel)}>Score</span>
                  <span {...stylex.props(
                    styles.statValue,
                    getRoundScoreStyle(score)
                  )}>
                    {formatScore(score.roundScore)}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Continue section */}
      <div {...stylex.props(styles.continueSection)}>
        <div {...stylex.props(styles.continueInfo)}>
          <div {...stylex.props(styles.nextRound)}>
            Starting Round {roundNumber + 1}
          </div>
          <div {...stylex.props(styles.autoContinue)}>
            <FooterTimer
              prefix="Continuing in"
              onComplete={onContinue}
              variant="inline"
            />
          </div>
        </div>
      </div>
    </>
  );
};

ScoringContent.propTypes = {
  players: PropTypes.array,
  scores: PropTypes.arrayOf(
    PropTypes.shape({
      playerName: PropTypes.string,
      declared: PropTypes.number,
      actual: PropTypes.number,
      hit: PropTypes.bool,
      hitValue: PropTypes.number,
      bonus: PropTypes.number,
      multiplier: PropTypes.number,
      roundScore: PropTypes.number,
      totalScore: PropTypes.number,
    })
  ),
  roundNumber: PropTypes.number,
  redealMultiplier: PropTypes.number,
  myName: PropTypes.string,
  onContinue: PropTypes.func,
};

export default ScoringContent;