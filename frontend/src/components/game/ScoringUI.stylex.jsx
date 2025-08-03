/**
 * 🏆 **ScoringUI Component** - Pure Scoring Phase Interface with StyleX
 *
 * Phase 2, Task 2.2: Pure UI Components
 *
 * Features:
 * ✅ Pure functional component (props in, JSX out)
 * ✅ No hooks except local UI state
 * ✅ Comprehensive prop interfaces
 * ✅ Accessible and semantic HTML
 * ✅ StyleX for type-safe, optimized styling
 */

import React from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
import Button from '../Button.stylex';
import PlayerAvatar from './shared/PlayerAvatar.stylex';
import FooterTimer from './shared/FooterTimer.stylex';
import { colors, spacing, shadows, layout, motion, typography } from '../../design-system/tokens.stylex';

// Animation keyframes
const slideIn = stylex.keyframes({
  '0%': {
    opacity: 0,
    transform: 'translateX(-20px)',
  },
  '100%': {
    opacity: 1,
    transform: 'translateX(0)',
  },
});

const fadeIn = stylex.keyframes({
  '0%': {
    opacity: 0,
  },
  '100%': {
    opacity: 1,
  },
});

const countUp = stylex.keyframes({
  '0%': {
    transform: 'scale(0.8)',
    opacity: 0,
  },
  '50%': {
    transform: 'scale(1.1)',
  },
  '100%': {
    transform: 'scale(1)',
    opacity: 1,
  },
});

const styles = stylex.create({
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.xl,
    padding: spacing.lg,
    minHeight: '100%',
  },
  
  // Header section
  headerSection: {
    textAlign: 'center',
    marginBottom: spacing.lg,
    animation: `${fadeIn} ${motion.durationNormal} ${motion.easeOut}`,
  },
  
  roundTitle: {
    fontSize: typography.textXl,
    fontWeight: typography.weightBold,
    color: colors.textDark,
    marginBottom: spacing.sm,
  },
  
  roundSubtitle: {
    fontSize: typography.textMd,
    color: colors.gray600,
  },
  
  // Multiplier badge
  multiplierBadge: {
    display: 'inline-flex',
    alignItems: 'center',
    backgroundColor: colors.warning,
    color: colors.textDark,
    padding: `${spacing.xs} ${spacing.md}`,
    borderRadius: layout.radiusFull,
    fontSize: typography.textSm,
    fontWeight: typography.weightBold,
    marginLeft: spacing.sm,
    boxShadow: shadows.sm,
  },
  
  // Scoring table
  scoringTable: {
    backgroundColor: colors.surface,
    borderRadius: layout.radiusLg,
    overflow: 'hidden',
    boxShadow: shadows.lg,
    animation: `${slideIn} ${motion.durationNormal} ${motion.easeOut}`,
  },
  
  tableHeader: {
    display: 'grid',
    gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr 1.5fr 1.5fr',
    backgroundColor: colors.primary,
    color: colors.textLight,
    padding: spacing.md,
    fontSize: typography.textSm,
    fontWeight: typography.weightBold,
    
    '@media (max-width: 768px)': {
      gridTemplateColumns: '2fr 1fr 1fr 1.5fr',
    },
  },
  
  tableHeaderCell: {
    textAlign: 'center',
    
    ':first-child': {
      textAlign: 'left',
    },
  },
  
  tableBody: {
    display: 'flex',
    flexDirection: 'column',
  },
  
  tableRow: {
    display: 'grid',
    gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr 1.5fr 1.5fr',
    padding: spacing.md,
    borderBottom: `1px solid ${colors.border}`,
    transition: motion.transitionBase,
    
    ':hover': {
      backgroundColor: colors.surfaceHover,
    },
    
    ':last-child': {
      borderBottom: 'none',
    },
    
    '@media (max-width: 768px)': {
      gridTemplateColumns: '2fr 1fr 1fr 1.5fr',
    },
  },
  
  tableRowHighlight: {
    backgroundColor: colors.primaryLight,
    
    ':hover': {
      backgroundColor: colors.primaryLight,
    },
  },
  
  tableCell: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: typography.textMd,
    color: colors.textDark,
    
    ':first-child': {
      justifyContent: 'flex-start',
    },
  },
  
  playerCell: {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.sm,
  },
  
  playerName: {
    fontWeight: typography.weightMedium,
  },
  
  // Score values
  scoreValue: {
    fontWeight: typography.weightBold,
    animation: `${countUp} ${motion.durationNormal} ${motion.easeOut}`,
  },
  
  scorePositive: {
    color: colors.success,
  },
  
  scoreNegative: {
    color: colors.danger,
  },
  
  scoreNeutral: {
    color: colors.gray600,
  },
  
  totalScore: {
    fontSize: typography.textLg,
    fontWeight: typography.weightBold,
    color: colors.primary,
  },
  
  // Hit/miss indicator
  hitIndicator: {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: '24px',
    height: '24px',
    borderRadius: layout.radiusFull,
    fontSize: typography.textSm,
  },
  
  hitSuccess: {
    backgroundColor: colors.success,
    color: colors.textLight,
  },
  
  hitMiss: {
    backgroundColor: colors.danger,
    color: colors.textLight,
  },
  
  // Bonus display
  bonusValue: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: spacing.xs,
    color: colors.warning,
    fontWeight: typography.weightMedium,
  },
  
  // Actions section
  actionsSection: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: spacing.md,
    marginTop: spacing.xl,
    animation: `${fadeIn} ${motion.durationSlow} ${motion.easeOut} 1s`,
    animationFillMode: 'both',
  },
  
  // Summary section
  summarySection: {
    display: 'flex',
    justifyContent: 'center',
    gap: spacing.xl,
    padding: spacing.lg,
    backgroundColor: colors.gray50,
    borderRadius: layout.radiusMd,
  },
  
  summaryItem: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: spacing.xs,
  },
  
  summaryLabel: {
    fontSize: typography.textSm,
    color: colors.gray600,
  },
  
  summaryValue: {
    fontSize: typography.textXl,
    fontWeight: typography.weightBold,
    color: colors.primary,
  },
  
  // Mobile hidden cells
  mobileHidden: {
    '@media (max-width: 768px)': {
      display: 'none',
    },
  },
});

/**
 * Pure UI component for scoring phase with integrated content
 */
export function ScoringUI({
  // Data props (all calculated by backend)
  players = [],
  roundScores = {},
  totalScores = {},
  redealMultiplier = 1,
  playersWithScores = [],
  roundNumber = 1,
  playerName = '',
  
  // State props
  gameOver = false,
  winners = [],
  
  // Action props
  onStartNextRound,
  
  // Additional props
  className = '',
}) {
  // Transform data for scoring display
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
          isBot: player.is_bot,
          avatarColor: player.avatar_color,
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
          isBot: player.is_bot,
          avatarColor: player.avatar_color,
        }));
  
  // Calculate summary stats
  const highestScore = Math.max(...scores.map(s => s.roundScore));
  const totalPointsScored = scores.reduce((sum, s) => sum + Math.max(0, s.roundScore), 0);
  
  return (
    <div {...stylex.props(styles.container, className && { className })}>
      {/* Header */}
      <div {...stylex.props(styles.headerSection)}>
        <h2 {...stylex.props(styles.roundTitle)}>
          Round {roundNumber} Complete
          {redealMultiplier > 1 && (
            <span {...stylex.props(styles.multiplierBadge)}>
              {redealMultiplier}x
            </span>
          )}
        </h2>
        <p {...stylex.props(styles.roundSubtitle)}>
          Scoring results below
        </p>
      </div>
      
      {/* Scoring table */}
      <div {...stylex.props(styles.scoringTable)}>
        <div {...stylex.props(styles.tableHeader)}>
          <div {...stylex.props(styles.tableHeaderCell)}>Player</div>
          <div {...stylex.props(styles.tableHeaderCell)}>Declared</div>
          <div {...stylex.props(styles.tableHeaderCell)}>Actual</div>
          <div {...stylex.props(styles.tableHeaderCell, styles.mobileHidden)}>Hit</div>
          <div {...stylex.props(styles.tableHeaderCell, styles.mobileHidden)}>Bonus</div>
          <div {...stylex.props(styles.tableHeaderCell, styles.mobileHidden)}>Round</div>
          <div {...stylex.props(styles.tableHeaderCell)}>Total</div>
        </div>
        
        <div {...stylex.props(styles.tableBody)}>
          {scores.map((score) => {
            const isCurrentPlayer = score.playerName === playerName;
            
            return (
              <div
                key={score.playerName}
                {...stylex.props(
                  styles.tableRow,
                  isCurrentPlayer && styles.tableRowHighlight
                )}
              >
                <div {...stylex.props(styles.tableCell)}>
                  <div {...stylex.props(styles.playerCell)}>
                    <PlayerAvatar
                      name={score.playerName}
                      isBot={score.isBot}
                      avatarColor={score.avatarColor}
                      size="small"
                    />
                    <span {...stylex.props(styles.playerName)}>
                      {score.playerName}
                    </span>
                  </div>
                </div>
                
                <div {...stylex.props(styles.tableCell)}>
                  {score.declared}
                </div>
                
                <div {...stylex.props(styles.tableCell)}>
                  {score.actual}
                </div>
                
                <div {...stylex.props(styles.tableCell, styles.mobileHidden)}>
                  <span {...stylex.props(
                    styles.hitIndicator,
                    score.hit ? styles.hitSuccess : styles.hitMiss
                  )}>
                    {score.hit ? '✓' : '✗'}
                  </span>
                </div>
                
                <div {...stylex.props(styles.tableCell, styles.mobileHidden)}>
                  {score.bonus > 0 && (
                    <span {...stylex.props(styles.bonusValue)}>
                      +{score.bonus}
                    </span>
                  )}
                </div>
                
                <div {...stylex.props(styles.tableCell, styles.mobileHidden)}>
                  <span {...stylex.props(
                    styles.scoreValue,
                    score.roundScore > 0 ? styles.scorePositive :
                    score.roundScore < 0 ? styles.scoreNegative :
                    styles.scoreNeutral
                  )}>
                    {score.roundScore > 0 && '+'}{score.roundScore}
                  </span>
                </div>
                
                <div {...stylex.props(styles.tableCell)}>
                  <span {...stylex.props(styles.totalScore)}>
                    {score.totalScore}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
      
      {/* Summary section */}
      <div {...stylex.props(styles.summarySection)}>
        <div {...stylex.props(styles.summaryItem)}>
          <span {...stylex.props(styles.summaryLabel)}>Highest Score</span>
          <span {...stylex.props(styles.summaryValue)}>{highestScore}</span>
        </div>
        <div {...stylex.props(styles.summaryItem)}>
          <span {...stylex.props(styles.summaryLabel)}>Total Points</span>
          <span {...stylex.props(styles.summaryValue)}>{totalPointsScored}</span>
        </div>
      </div>
      
      {/* Actions */}
      <div {...stylex.props(styles.actionsSection)}>
        {!gameOver && (
          <>
            <FooterTimer
              duration={10}
              prefix="Next round in"
              onComplete={onStartNextRound}
              variant="prominent"
            />
            <Button
              onClick={onStartNextRound}
              variant="primary"
              size="large"
            >
              Start Next Round
            </Button>
          </>
        )}
      </div>
    </div>
  );
}

// PropTypes definition
ScoringUI.propTypes = {
  // Data props (all calculated by backend)
  players: PropTypes.arrayOf(
    PropTypes.shape({
      name: PropTypes.string.isRequired,
      pile_count: PropTypes.number,
      actualPiles: PropTypes.number,
      is_bot: PropTypes.bool,
      avatar_color: PropTypes.string,
    })
  ),
  roundScores: PropTypes.object,
  totalScores: PropTypes.object,
  redealMultiplier: PropTypes.number,
  playersWithScores: PropTypes.array,
  roundNumber: PropTypes.number,
  playerName: PropTypes.string,
  
  // State props
  gameOver: PropTypes.bool,
  winners: PropTypes.array,
  
  // Action props
  onStartNextRound: PropTypes.func,
  
  // Additional props
  className: PropTypes.string,
};

ScoringUI.defaultProps = {
  players: [],
  roundScores: {},
  totalScores: {},
  redealMultiplier: 1,
  playersWithScores: [],
  roundNumber: 1,
  playerName: '',
  gameOver: false,
  winners: [],
  onStartNextRound: null,
  className: '',
};

export default ScoringUI;