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
    padding: '2rem',
    minHeight: '400px',
  },
  
  roundSection: {
    textAlign: 'center',
    marginBottom: '4rem',
    animation: `${fadeInScale} 0.5s 'cubic-bezier(0, 0, 0.2, 1)'`,
  },
  
  roundLabel: {
    fontSize: '1.125rem',
    fontWeight: '500',
    color: '#6c757d',
    marginBottom: '0.5rem',
    textTransform: 'uppercase',
    letterSpacing: '0.1em',
  },
  
  roundNumber: {
    fontSize: '5rem',
    fontWeight: '700',
    background: gradients.primary,
    backgroundClip: 'text',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    lineHeight: 1,
    textShadow: `0 4px 8px '#e7f1ff'33`,
  },
  
  starterSection: {
    textAlign: 'center',
    marginBottom: '4rem',
    animation: `${slideInFromTop} 0.5s 'cubic-bezier(0, 0, 0.2, 1)' 0.2s`,
    animationFillMode: 'both',
  },
  
  starterLabel: {
    fontSize: '0.875rem',
    fontWeight: '500',
    color: '#adb5bd',
    marginBottom: '0.5rem',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
  
  starterName: {
    fontSize: '1.5rem',
    fontWeight: '700',
    color: '#343a40',
    marginBottom: '1rem',
  },
  
  generalPiece: {
    display: 'inline-block',
    padding: '1rem',
    backgroundColor: '#ffffff',
    borderRadius: '9999px',
    boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    animation: `${fadeInScale} 0.3s 'cubic-bezier(0, 0, 0.2, 1)' 0.4s`,
    animationFillMode: 'both',
  },
  
  starterReason: {
    fontSize: '1rem',
    color: '#6c757d',
    fontStyle: 'italic',
    padding: '0.5rem',
    backgroundColor: '#f8f9fa',
    borderRadius: '0.375rem',
    display: 'inline-block',
  },
  
  timerSection: {
    display: 'flex',
    justifyContent: 'center',
    marginTop: 'auto',
    animation: `${fadeInScale} 0.3s 'cubic-bezier(0, 0, 0.2, 1)' 0.6s`,
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