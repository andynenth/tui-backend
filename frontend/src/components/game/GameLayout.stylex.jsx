import React from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, layout, shadows, gradients, motion } from '../../design-system/tokens.stylex';
import { formatPlayType } from '../../utils/playTypeFormatter';

// GameLayout styles
const styles = stylex.create({
  container: {
    width: '100%',
    maxWidth: '450px',
    margin: '0 auto',
    aspectRatio: '9 / 16',
    backgroundColor: colors.gray100,
    borderRadius: layout.radiusLg,
    padding: spacing.lg,
    position: 'relative',
    display: 'flex',
    flexDirection: 'column',
    boxShadow: shadows.lg,
  },
  
  roundIndicator: {
    position: 'absolute',
    top: spacing.md,
    left: spacing.md,
    backgroundColor: colors.primary,
    color: colors.white,
    paddingTop: spacing.xs,
    paddingBottom: spacing.xs,
    paddingLeft: spacing.sm,
    paddingRight: spacing.sm,
    borderRadius: layout.radiusFull,
    fontSize: typography.textSm,
    fontWeight: typography.weightBold,
    boxShadow: shadows.sm,
    zIndex: 10,
  },
  
  multiplierBadge: {
    position: 'absolute',
    top: spacing.md,
    right: spacing.md,
    paddingTop: spacing.xs,
    paddingBottom: spacing.xs,
    paddingLeft: spacing.sm,
    paddingRight: spacing.sm,
    borderRadius: layout.radiusFull,
    fontSize: typography.textSm,
    fontWeight: typography.weightBold,
    boxShadow: shadows.sm,
    background: gradients.accent,
    color: colors.white,
    opacity: 0,
    transform: 'scale(0.8)',
    transition: `all ${motion.durationBase} ${motion.easeInOut}`,
    zIndex: 10,
  },
  
  multiplierBadgeShow: {
    opacity: 1,
    transform: 'scale(1)',
  },
  
  phaseHeader: {
    textAlign: 'center',
    marginBottom: spacing.xl,
    marginTop: spacing.xxl,
  },
  
  phaseTitle: {
    fontSize: typography.text2xl,
    fontWeight: typography.weightBold,
    marginBottom: spacing.sm,
    color: colors.gray800,
    transition: `color ${motion.durationBase} ${motion.easeInOut}`,
  },
  
  phaseTitleTurnType: {
    background: gradients.primary,
    backgroundClip: 'text',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    fontSize: typography.text3xl,
  },
  
  phaseSubtitle: {
    fontSize: typography.textBase,
    color: colors.gray600,
    fontWeight: typography.weightNormal,
  },
  
  contentSection: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'auto',
    paddingBottom: spacing.md,
  },
  
  // Phase-specific styles
  preparationPhase: {
    backgroundColor: 'rgba(37, 99, 235, 0.05)',
  },
  
  declarationPhase: {
    backgroundColor: 'rgba(16, 185, 129, 0.05)',
  },
  
  turnPhase: {
    backgroundColor: 'rgba(251, 146, 60, 0.05)',
  },
  
  scoringPhase: {
    backgroundColor: 'rgba(168, 85, 247, 0.05)',
  },
  
  gameOverPhase: {
    backgroundColor: 'rgba(59, 130, 246, 0.05)',
  },
});

/**
 * GameLayout Component
 *
 * Provides consistent layout wrapper for all game phases:
 * - Fixed 9:16 aspect ratio container
 * - Round indicator badge
 * - Multiplier badge (when applicable)
 * - Phase header with title/subtitle
 * - Content area for phase-specific content
 */
const GameLayout = ({
  children,
  phase,
  roundNumber = 1,
  showMultiplier = false,
  multiplierValue = 2,
  // Additional props for turn phase
  playType = '',
  currentPlayer = '',
  turnRequirement = null,
  // Additional props for turn results phase
  winner = '',
  // During migration, allow existing CSS classes
  className = '',
}) => {
  // Get phase title and subtitle based on current phase
  const getPhaseInfo = () => {
    switch (phase) {
      case 'preparation':
        return {
          title: 'Preparation Phase',
          subtitle: 'Dealing cards to all players',
        };
      case 'declaration':
        return {
          title: 'Declaration',
          subtitle: 'Choose your target piles',
        };
      case 'turn':
        return {
          title: playType ? formatPlayType(playType) : 'Turn Phase',
          subtitle: currentPlayer
            ? `Round ${roundNumber} • ${currentPlayer}'s Turn`
            : 'Play your pieces strategically',
        };
      case 'turn_results':
        return {
          title: 'Turn Results',
          subtitle: winner
            ? `${winner} wins this turn!`
            : 'See who won this turn',
        };
      case 'scoring':
        return {
          title: 'Scoring',
          subtitle: 'Round complete',
        };
      case 'game_over':
        return {
          title: 'Game Over',
          subtitle: 'Final results',
        };
      default:
        return {
          title: 'Loading',
          subtitle: 'Please wait...',
        };
    }
  };

  const { title, subtitle } = getPhaseInfo();
  
  // Get phase-specific background style
  const getPhaseStyle = () => {
    switch (phase) {
      case 'preparation':
        return styles.preparationPhase;
      case 'declaration':
        return styles.declarationPhase;
      case 'turn':
      case 'turn_results':
        return styles.turnPhase;
      case 'scoring':
        return styles.scoringPhase;
      case 'game_over':
        return styles.gameOverPhase;
      default:
        return null;
    }
  };
  
  const phaseStyle = getPhaseStyle();
  
  // Apply container styles
  const containerProps = stylex.props(
    styles.container,
    phaseStyle
  );
  
  // During migration, allow combining with existing CSS classes
  const combinedContainerProps = className 
    ? { ...containerProps, className: `${containerProps.className || ''} ${className}`.trim() }
    : containerProps;

  return (
    <div {...combinedContainerProps}>
      {/* Round indicator */}
      <div {...stylex.props(styles.roundIndicator)}>
        Round {roundNumber}
      </div>

      {/* Multiplier badge (shown conditionally) */}
      <div {...stylex.props(
        styles.multiplierBadge,
        showMultiplier && styles.multiplierBadgeShow
      )}>
        {multiplierValue}x Multiplier
      </div>

      {/* Phase header */}
      <div {...stylex.props(styles.phaseHeader)}>
        <h1 {...stylex.props(
          styles.phaseTitle,
          phase === 'turn' && playType && styles.phaseTitleTurnType
        )}>
          {title}
        </h1>
        <p {...stylex.props(styles.phaseSubtitle)}>
          {subtitle}
        </p>
      </div>

      {/* Content section */}
      <div {...stylex.props(styles.contentSection)}>
        {children}
      </div>
    </div>
  );
};

GameLayout.propTypes = {
  children: PropTypes.node.isRequired,
  phase: PropTypes.oneOf([
    'preparation',
    'declaration',
    'turn',
    'turn_results',
    'scoring',
    'game_over',
  ]).isRequired,
  roundNumber: PropTypes.number,
  showMultiplier: PropTypes.bool,
  multiplierValue: PropTypes.number,
  playType: PropTypes.string,
  currentPlayer: PropTypes.string,
  turnRequirement: PropTypes.shape({
    type: PropTypes.string,
    text: PropTypes.string,
  }),
  winner: PropTypes.string,
  className: PropTypes.string,
};

export default GameLayout;