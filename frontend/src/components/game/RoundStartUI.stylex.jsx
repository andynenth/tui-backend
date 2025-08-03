/**
 * 📋 **RoundStartUI Component** - Round Start Phase Interface with StyleX
 *
 * Displays round information before declaration phase:
 * - Round number
 * - Starter name
 * - Reason for being starter
 *
 * Auto-transitions to Declaration after 5 seconds
 */

import React from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
import FooterTimer from './shared/FooterTimer.stylex';
import GamePiece from './shared/GamePiece.stylex';
import { colors, spacing, shadows, layout, motion, typography } from '../../design-system/tokens.stylex';

// Animation keyframes
const fadeIn = stylex.keyframes({
  '0%': {
    opacity: 0,
    transform: 'scale(0.9)',
  },
  '100%': {
    opacity: 1,
    transform: 'scale(1)',
  },
});

const slideUp = stylex.keyframes({
  '0%': {
    opacity: 0,
    transform: 'translateY(20px)',
  },
  '100%': {
    opacity: 1,
    transform: 'translateY(0)',
  },
});

const glow = stylex.keyframes({
  '0%, 100%': {
    boxShadow: `0 0 20px ${colors.primary}`,
  },
  '50%': {
    boxShadow: `0 0 40px ${colors.primary}, 0 0 60px ${colors.primaryLight}`,
  },
});

const styles = stylex.create({
  container: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.xxl,
    padding: spacing.xl,
    minHeight: '400px',
    animation: `${fadeIn} ${motion.durationNormal} ${motion.easeOut}`,
  },
  
  // Round section
  roundSection: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: spacing.md,
    animation: `${slideUp} ${motion.durationNormal} ${motion.easeOut}`,
    animationDelay: '0.1s',
    animationFillMode: 'both',
  },
  
  roundLabel: {
    fontSize: typography.textMd,
    fontWeight: typography.weightMedium,
    color: colors.gray600,
    textTransform: 'uppercase',
    letterSpacing: '0.1em',
  },
  
  roundNumber: {
    fontSize: '5rem',
    fontWeight: typography.weightBold,
    color: colors.primary,
    lineHeight: 1,
    textShadow: `2px 2px 4px ${colors.shadow}`,
    animation: `${glow} 2s ${motion.easeInOut} infinite`,
  },
  
  // Starter section
  starterSection: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: spacing.md,
    animation: `${slideUp} ${motion.durationNormal} ${motion.easeOut}`,
    animationDelay: '0.3s',
    animationFillMode: 'both',
  },
  
  starterLabel: {
    fontSize: typography.textSm,
    fontWeight: typography.weightMedium,
    color: colors.gray600,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
  
  starterName: {
    fontSize: typography.textXxl,
    fontWeight: typography.weightBold,
    color: colors.textDark,
    textAlign: 'center',
  },
  
  starterReason: {
    fontSize: typography.textMd,
    color: colors.gray600,
    fontStyle: 'italic',
    textAlign: 'center',
  },
  
  // General piece display
  generalPiece: {
    marginTop: spacing.sm,
    animation: `${glow} 2s ${motion.easeInOut} infinite`,
    borderRadius: layout.radiusMd,
    padding: spacing.sm,
  },
  
  // Timer section
  timerSection: {
    marginTop: spacing.lg,
    animation: `${slideUp} ${motion.durationNormal} ${motion.easeOut}`,
    animationDelay: '0.5s',
    animationFillMode: 'both',
  },
  
  // Visual decoration
  decorationTop: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: '4px',
    background: `linear-gradient(90deg, transparent, ${colors.primary}, transparent)`,
    animation: `${fadeIn} ${motion.durationSlow} ${motion.easeOut}`,
  },
  
  decorationBottom: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: '4px',
    background: `linear-gradient(90deg, transparent, ${colors.primary}, transparent)`,
    animation: `${fadeIn} ${motion.durationSlow} ${motion.easeOut}`,
  },
  
  // Responsive adjustments
  '@media (max-width: 640px)': {
    container: {
      padding: spacing.lg,
      gap: spacing.xl,
    },
    
    roundNumber: {
      fontSize: '4rem',
    },
    
    starterName: {
      fontSize: typography.textXl,
    },
  },
});

/**
 * Pure UI component for round start phase with integrated content
 */
export function RoundStartUI({
  // Data props
  roundNumber = 1,
  starter = '',
  starterReason = 'default',
  
  // Additional props
  className = '',
}) {
  // Get human-readable reason text
  const getReasonText = () => {
    switch (starterReason) {
      case 'has_general_red':
        return 'has the General Red piece';
      case 'won_last_turn':
        return 'won the last turn';
      case 'accepted_redeal':
        return 'accepted the redeal';
      default:
        return 'starts this round';
    }
  };
  
  return (
    <div {...stylex.props(styles.container, className && { className })}>
      {/* Decorative elements */}
      <div {...stylex.props(styles.decorationTop)} />
      
      {/* Round number display */}
      <div {...stylex.props(styles.roundSection)}>
        <div {...stylex.props(styles.roundLabel)}>Round</div>
        <div {...stylex.props(styles.roundNumber)}>{roundNumber}</div>
      </div>
      
      {/* Starter information */}
      <div {...stylex.props(styles.starterSection)}>
        <div {...stylex.props(styles.starterLabel)}>Starter</div>
        <div {...stylex.props(styles.starterName)}>{starter}</div>
        {starterReason === 'has_general_red' ? (
          <div {...stylex.props(styles.generalPiece)}>
            <GamePiece
              piece={{ kind: 'GENERAL', color: 'red', value: 14 }}
              size="large"
              showValue={false}
            />
          </div>
        ) : (
          <div {...stylex.props(styles.starterReason)}>
            {getReasonText()}
          </div>
        )}
      </div>
      
      {/* Auto-advance timer */}
      <div {...stylex.props(styles.timerSection)}>
        <FooterTimer
          duration={5}
          prefix="Starting in"
          onComplete={() => {}}
          variant="prominent"
          size="medium"
        />
      </div>
      
      {/* Decorative elements */}
      <div {...stylex.props(styles.decorationBottom)} />
    </div>
  );
}

// PropTypes definition
RoundStartUI.propTypes = {
  roundNumber: PropTypes.number.isRequired,
  starter: PropTypes.string.isRequired,
  starterReason: PropTypes.oneOf([
    'has_general_red',
    'won_last_turn',
    'accepted_redeal',
    'default',
  ]).isRequired,
  className: PropTypes.string,
};

RoundStartUI.defaultProps = {
  roundNumber: 1,
  starter: '',
  starterReason: 'default',
  className: '',
};

export default RoundStartUI;