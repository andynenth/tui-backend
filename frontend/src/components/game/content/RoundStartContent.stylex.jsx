import React from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, motion, layout, shadows, gradients } from '../../../design-system/tokens.stylex';
import { FooterTimer, GamePiece } from '../shared';

// Animations
const fadeInScale = stylex.keyframes({
  '0%': {
    opacity: 0,
    transform: 'scale(0.8)',
  },
  '100%': {
    opacity: 1,
    transform: 'scale(1)',
  },
});

const slideInFromTop = stylex.keyframes({
  '0%': {
    opacity: 0,
    transform: 'translateY(-30px)',
  },
  '100%': {
    opacity: 1,
    transform: 'translateY(0)',
  },
});

// RoundStartContent styles
const styles = stylex.create({
  content: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.xl,
    minHeight: '400px',
  },
  
  roundSection: {
    textAlign: 'center',
    marginBottom: spacing.xxxl,
    animation: `${fadeInScale} 0.5s ${motion.easeOut}`,
  },
  
  roundLabel: {
    fontSize: typography.textLg,
    fontWeight: typography.weightMedium,
    color: colors.gray600,
    marginBottom: spacing.sm,
    textTransform: 'uppercase',
    letterSpacing: '0.1em',
  },
  
  roundNumber: {
    fontSize: '5rem',
    fontWeight: typography.weightBold,
    background: gradients.primary,
    backgroundClip: 'text',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    lineHeight: 1,
    textShadow: `0 4px 8px ${colors.primaryLight}33`,
  },
  
  starterSection: {
    textAlign: 'center',
    marginBottom: spacing.xxxl,
    animation: `${slideInFromTop} 0.5s ${motion.easeOut} 0.2s`,
    animationFillMode: 'both',
  },
  
  starterLabel: {
    fontSize: typography.textSm,
    fontWeight: typography.weightMedium,
    color: colors.gray500,
    marginBottom: spacing.sm,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
  
  starterName: {
    fontSize: typography.text2xl,
    fontWeight: typography.weightBold,
    color: colors.gray800,
    marginBottom: spacing.md,
  },
  
  generalPiece: {
    display: 'inline-block',
    padding: spacing.md,
    backgroundColor: colors.white,
    borderRadius: layout.radiusFull,
    boxShadow: shadows.lg,
    animation: `${fadeInScale} 0.3s ${motion.easeOut} 0.4s`,
    animationFillMode: 'both',
  },
  
  starterReason: {
    fontSize: typography.textBase,
    color: colors.gray600,
    fontStyle: 'italic',
    padding: spacing.sm,
    backgroundColor: colors.gray50,
    borderRadius: layout.radiusMd,
    display: 'inline-block',
  },
  
  timerSection: {
    display: 'flex',
    justifyContent: 'center',
    marginTop: 'auto',
    animation: `${fadeInScale} 0.3s ${motion.easeOut} 0.6s`,
    animationFillMode: 'both',
  },
});

/**
 * RoundStartContent Component
 *
 * Displays round start information:
 * - Large round number
 * - Starter name with reason
 * - 5-second countdown timer
 */
const RoundStartContent = ({ roundNumber, starter, starterReason }) => {
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
    <div {...stylex.props(styles.content)}>
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
          variant="inline"
        />
      </div>
    </div>
  );
};

RoundStartContent.propTypes = {
  roundNumber: PropTypes.number.isRequired,
  starter: PropTypes.string.isRequired,
  starterReason: PropTypes.string.isRequired,
};

export default RoundStartContent;