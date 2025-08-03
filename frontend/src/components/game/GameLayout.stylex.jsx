// GameLayout component with StyleX
import React from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
import { formatPlayType } from '../../utils/playTypeFormatter';
import { colors, spacing, shadows, layout, motion, typography } from '../../design-system/tokens.stylex';

// Animation keyframes
const slideDown = stylex.keyframes({
  '0%': {
    transform: 'translateY(-100%)',
    opacity: 0,
  },
  '100%': {
    transform: 'translateY(0)',
    opacity: 1,
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

const bounce = stylex.keyframes({
  '0%, 100%': {
    transform: 'scale(1)',
  },
  '50%': {
    transform: 'scale(1.1)',
  },
});

const shimmer = stylex.keyframes({
  '0%': {
    backgroundPosition: '-200px 0',
  },
  '100%': {
    backgroundPosition: '200px 0',
  },
});

const styles = stylex.create({
  container: {
    position: 'relative',
    width: '100%',
    maxWidth: '900px',
    margin: '0 auto',
    minHeight: '100vh',
    padding: spacing.lg,
    backgroundColor: colors.background,
    display: 'flex',
    flexDirection: 'column',
    animation: `${fadeIn} ${motion.durationNormal} ${motion.easeOut}`,
    
    '@media (max-width: 768px)': {
      padding: spacing.md,
    },
  },
  
  // Fixed aspect ratio container
  aspectContainer: {
    position: 'relative',
    width: '100%',
    paddingBottom: '177.78%', // 9:16 aspect ratio
    backgroundColor: colors.surface,
    borderRadius: layout.radiusXl,
    boxShadow: shadows.xl,
    overflow: 'hidden',
  },
  
  innerContent: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    padding: spacing.xl,
    display: 'flex',
    flexDirection: 'column',
    
    '@media (max-width: 640px)': {
      padding: spacing.md,
    },
  },
  
  // Round indicator badge
  roundIndicator: {
    position: 'absolute',
    top: spacing.md,
    right: spacing.md,
    backgroundColor: colors.primary,
    color: colors.textLight,
    padding: `${spacing.xs} ${spacing.md}`,
    borderRadius: layout.radiusFull,
    fontSize: typography.textSm,
    fontWeight: typography.weightBold,
    boxShadow: shadows.md,
    animation: `${slideDown} ${motion.durationNormal} ${motion.easeOut}`,
    zIndex: 2,
  },
  
  // Multiplier badge
  multiplierBadge: {
    position: 'absolute',
    top: spacing.md,
    left: spacing.md,
    backgroundColor: colors.warning,
    color: colors.textDark,
    padding: `${spacing.xs} ${spacing.md}`,
    borderRadius: layout.radiusFull,
    fontSize: typography.textSm,
    fontWeight: typography.weightBold,
    boxShadow: shadows.md,
    transform: 'scale(0)',
    opacity: 0,
    transition: `all ${motion.durationFast} ${motion.easeOut}`,
    zIndex: 2,
    backgroundImage: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent)',
    backgroundSize: '200px 100%',
    animation: `${shimmer} 2s linear infinite`,
  },
  
  multiplierBadgeShow: {
    transform: 'scale(1)',
    opacity: 1,
    animation: `${bounce} ${motion.durationNormal} ${motion.easeOut}, ${shimmer} 2s linear infinite`,
  },
  
  // Phase header
  phaseHeader: {
    textAlign: 'center',
    marginBottom: spacing.xl,
    animation: `${fadeIn} ${motion.durationSlow} ${motion.easeOut} 200ms`,
    animationFillMode: 'both',
  },
  
  phaseTitle: {
    fontSize: typography.textXxl,
    fontWeight: typography.weightBold,
    color: colors.textDark,
    marginBottom: spacing.sm,
    lineHeight: typography.lineHeightTight,
    
    '@media (max-width: 640px)': {
      fontSize: typography.textXl,
    },
  },
  
  phaseTitleTurnType: {
    color: colors.primary,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
  
  phaseSubtitle: {
    fontSize: typography.textMd,
    color: colors.gray600,
    lineHeight: typography.lineHeightNormal,
    
    '@media (max-width: 640px)': {
      fontSize: typography.textSm,
    },
  },
  
  // Content section
  contentSection: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.lg,
    animation: `${fadeIn} ${motion.durationSlow} ${motion.easeOut} 400ms`,
    animationFillMode: 'both',
  },
  
  // Phase-specific styles
  phasePreparation: {
    backgroundColor: colors.backgroundGradient,
  },
  
  phaseDeclaration: {
    backgroundColor: colors.surface,
    border: `2px solid ${colors.primary}`,
  },
  
  phaseTurn: {
    backgroundColor: colors.surface,
    backgroundImage: `linear-gradient(135deg, ${colors.surface} 0%, ${colors.surfaceHover} 100%)`,
  },
  
  phaseTurnResults: {
    backgroundColor: colors.success,
    backgroundImage: `linear-gradient(135deg, ${colors.success} 0%, ${colors.successDark} 100%)`,
  },
  
  phaseScoring: {
    backgroundColor: colors.warning,
    backgroundImage: `linear-gradient(135deg, ${colors.warning} 0%, ${colors.warningDark} 100%)`,
  },
  
  phaseGameOver: {
    backgroundColor: colors.secondary,
    backgroundImage: `linear-gradient(135deg, ${colors.secondary} 0%, ${colors.secondaryDark} 100%)`,
  },
});

const GameLayout = ({
  children,
  phase,
  roundNumber = 1,
  showMultiplier = false,
  multiplierValue = 2,
  // Additional props for turn phase
  playType = '',
  currentPlayer = '',
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  turnRequirement = null,
  // Additional props for turn results phase
  winner = '',
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
  
  // Get phase-specific container style
  const getPhaseStyle = () => {
    const phaseMap = {
      'preparation': styles.phasePreparation,
      'declaration': styles.phaseDeclaration,
      'turn': styles.phaseTurn,
      'turn_results': styles.phaseTurnResults,
      'scoring': styles.phaseScoring,
      'game_over': styles.phaseGameOver,
    };
    return phaseMap[phase] || null;
  };
  
  return (
    <div {...stylex.props(
      styles.container,
      className && { className }
    )}>
      <div {...stylex.props(
        styles.aspectContainer,
        getPhaseStyle()
      )}>
        <div {...stylex.props(styles.innerContent)}>
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