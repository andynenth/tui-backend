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
    padding: '1.5rem',
    flex: 1,
    overflowY: 'auto',
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
  },
  
  scoreCard: {
    backgroundColor: '#ffffff',
    borderRadius: '0.5rem',
    padding: '1.5rem',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    animation: `${slideIn} 0.3s 'cubic-bezier(0, 0, 0.2, 1)'`,
    animationFillMode: 'both',
  },
  
  topRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1rem',
    paddingBottom: '1rem',
    borderBottomWidth: '1px',
    borderBottomStyle: 'solid',
    borderBottomColor: '#e9ecef',
  },
  
  playerInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
  },
  
  playerName: {
    fontSize: '1.125rem',
    fontWeight: '500',
    color: '#343a40',
  },
  
  totalScore: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'flex-end',
    gap: spacing.xxs,
  },
  
  totalLabel: {
    fontSize: '0.875rem',
    color: '#adb5bd',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
  
  totalValue: {
    fontSize: '1.5rem',
    fontWeight: '700',
  },
  
  totalNeutral: {
    color: '#495057',
  },
  
  bottomRow: {
    display: 'flex',
    justifyContent: 'space-between',
    gap: '1rem',
  },
  
  stat: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: spacing.xxs,
    flex: 1,
  },
  
  statTarget: {
    borderRightWidth: '1px',
    borderRightStyle: 'solid',
    borderRightColor: '#e9ecef',
    paddingRight: '1rem',
  },
  
  statLabel: {
    fontSize: '0.75rem',
    color: '#adb5bd',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
  
  targetValue: {
    fontSize: '1.125rem',
    fontWeight: '700',
  },
  
  statValue: {
    fontSize: '1rem',
    fontWeight: '500',
  },
  
  valuePositive: {
    color: '#198754',
  },
  
  valueNegative: {
    color: '#dc3545',
  },
  
  valueNeutral: {
    color: '#6c757d',
  },
  
  valueBlue: {
    color: '#0d6efd',
  },
  
  multiplier: {
    fontSize: '1rem',
    fontWeight: '700',
    color: '#ffc107',
    padding: `${spacing.xxs} '0.5rem'`,
    backgroundColor: 'rgba(245, 158, 11, 0.1)',
    borderRadius: '0.125rem',
  },
  
  continueSection: {
    padding: '1.5rem',
    backgroundColor: '#f8f9fa',
    borderTopWidth: '1px',
    borderTopStyle: 'solid',
    borderTopColor: '#e9ecef',
  },
  
  continueInfo: {
    textAlign: 'center',
  },
  
  nextRound: {
    fontSize: '1.125rem',
    fontWeight: '500',
    color: '#495057',
    marginBottom: '1rem',
  },
  
  autoContinue: {
    display: 'flex',
    justifyContent: 'center',
  },
  
  perfectScore: {
    backgroundImage: `linear-gradient(90deg, '#198754'33 0%, '#198754'66 50%, '#198754'33 100%)`,
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
  myName = ',
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
                    {player.name === myName ? ' (You)' : '}
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