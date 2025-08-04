import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, motion, layout, shadows, gradients } from '../../../design-system/tokens.stylex';
import { PieceTray } from '../shared';
import { TIMING } from '../../../constants';

// Keyframe animations
const cardDeal = stylex.keyframes({
  '0%': {
    transform: 'translateY(-100px) rotate(-20deg)',
    opacity: 0,
  },
  '50%': {
    transform: 'translateY(0) rotate(10deg)',
    opacity: 1,
  },
  '100%': {
    transform: 'translateY(0) rotate(0deg)',
    opacity: 1,
  },
});

const progressFill = stylex.keyframes({
  '0%': {
    width: '0%',
  },
  '100%': {
    width: '100%',
  },
});

// PreparationContent styles
const styles = stylex.create({
  contentSection: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.lg,
  },
  
  dealingContainer: {
    textAlign: 'center',
    animation: `${cardDeal} 0.5s ${motion.easeOut}`,
  },
  
  dealingIcon: {
    display: 'flex',
    justifyContent: 'center',
    gap: spacing.xs,
    marginBottom: spacing.xl,
  },
  
  cardStack: {
    width: '60px',
    height: '90px',
    backgroundColor: colors.primary,
    borderRadius: layout.radiusMd,
    boxShadow: shadows.md,
    position: 'relative',
    animation: `${cardDeal} 0.5s ${motion.easeOut}`,
    animationDelay: 'calc(var(--index) * 0.1s)',
    
    '::before': {
      content: '""',
      position: 'absolute',
      top: '-4px',
      left: '-4px',
      right: '4px',
      bottom: '4px',
      backgroundColor: colors.primaryLight,
      borderRadius: layout.radiusMd,
      zIndex: -1,
    },
    
    '::after': {
      content: '""',
      position: 'absolute',
      top: '-8px',
      left: '-8px',
      right: '8px',
      bottom: '8px',
      backgroundColor: colors.primaryLighter,
      borderRadius: layout.radiusMd,
      zIndex: -2,
    },
  },
  
  cardStack1: {
    '--index': '0',
  },
  
  cardStack2: {
    '--index': '1',
  },
  
  cardStack3: {
    '--index': '2',
  },
  
  dealingMessage: {
    fontSize: typography.text2xl,
    fontWeight: typography.weightBold,
    color: colors.gray800,
    marginBottom: spacing.sm,
  },
  
  dealingStatus: {
    fontSize: typography.textBase,
    color: colors.gray600,
    marginBottom: spacing.xl,
  },
  
  progressContainer: {
    width: '200px',
    height: '8px',
    backgroundColor: colors.gray200,
    borderRadius: layout.radiusFull,
    overflow: 'hidden',
    margin: '0 auto',
  },
  
  progressBar: {
    height: '100%',
    position: 'relative',
  },
  
  progressFill: {
    height: '100%',
    background: gradients.primary,
    borderRadius: layout.radiusFull,
    animation: `${progressFill} ${TIMING.DEALING_ANIMATION_DURATION}ms ${motion.easeInOut}`,
  },
  
  weakHandAlert: {
    backgroundColor: colors.white,
    borderRadius: layout.radiusLg,
    padding: spacing.xl,
    boxShadow: shadows.lg,
    border: `2px solid ${colors.warning}`,
    maxWidth: '400px',
    margin: '0 auto',
    opacity: 0,
    transform: 'scale(0.9)',
    transition: `all ${motion.durationBase} ${motion.easeOut}`,
  },
  
  weakHandAlertShow: {
    opacity: 1,
    transform: 'scale(1)',
  },
  
  alertTitle: {
    fontSize: typography.textXl,
    fontWeight: typography.weightBold,
    color: colors.warning,
    marginBottom: spacing.md,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
  },
  
  alertMessage: {
    fontSize: typography.textBase,
    color: colors.gray700,
    marginBottom: spacing.lg,
    lineHeight: 1.5,
  },
  
  multiplierWarning: {
    marginTop: spacing.sm,
    padding: spacing.sm,
    backgroundColor: 'rgba(245, 158, 11, 0.1)',
    borderRadius: layout.radiusMd,
    fontSize: typography.textSm,
    color: colors.warningDark,
    fontWeight: typography.weightMedium,
  },
  
  alertButtons: {
    display: 'flex',
    gap: spacing.md,
    justifyContent: 'center',
  },
  
  alertButton: {
    padding: `${spacing.sm} ${spacing.lg}`,
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
    color: colors.gray700,
    
    ':hover': {
      backgroundColor: colors.gray300,
    },
  },
  
  waitingIndicator: {
    textAlign: 'center',
    padding: spacing.lg,
    backgroundColor: colors.gray50,
    borderRadius: layout.radiusMd,
  },
  
  waitingText: {
    fontSize: typography.textLg,
    color: colors.gray700,
    marginBottom: spacing.sm,
  },
  
  waitingProgress: {
    fontSize: typography.textSm,
    color: colors.gray600,
  },
});

/**
 * PreparationContent Component
 *
 * Displays the preparation phase with:
 * - Dealing animation (3.5s) in content-section
 * - Weak hand alert after dealing
 * - Player's hand always visible at bottom
 */
const PreparationContent = ({
  myHand = [],
  players = [],
  weakHands = [],
  redealMultiplier = 1,
  currentWeakPlayer,
  isMyDecision = false,
  isMyHandWeak = false,
  handValue = 0,
  highestCardValue = 0,
  simultaneousMode = false,
  weakPlayersAwaiting = [],
  decisionsReceived = 0,
  decisionsNeeded = 0,
  dealingCards = false,
  onAcceptRedeal,
  onDeclineRedeal,
}) => {
  const [showDealing, setShowDealing] = useState(true);
  const [isRedealing, setIsRedealing] = useState(false);
  const [dealCount, setDealCount] = useState(0);

  // Auto-hide dealing animation after 3.5s
  useEffect(() => {
    const timer = setTimeout(() => {
      setShowDealing(false);
    }, TIMING.DEALING_ANIMATION_DURATION);

    return () => {
      clearTimeout(timer);
    };
  }, []);

  // Watch for redeal animation trigger
  useEffect(() => {
    if (dealingCards === true && !showDealing) {
      // Not initial deal, must be redeal!
      setIsRedealing(true);
      // Increment deal count to force re-animation
      setDealCount((prev) => prev + 1);
    }
  }, [dealingCards, showDealing]);

  // Separate effect for redeal animation timer
  useEffect(() => {
    if (isRedealing) {
      const timer = setTimeout(() => {
        setIsRedealing(false);
      }, TIMING.DEALING_ANIMATION_DURATION);

      return () => {
        clearTimeout(timer);
      };
    }
  }, [isRedealing, isMyHandWeak, weakPlayersAwaiting]);

  // Check if we should show weak hand alert
  const shouldShowWeakHandAlert = () => {
    const shouldShow = !showDealing && !isRedealing && isMyHandWeak;

    if (!showDealing && !isRedealing) {
      // Show alert if:
      // 1. Player has a weak hand (no piece > 9)
      // 2. It's their turn to decide (or in simultaneous mode, they haven't decided yet)
      if (isMyHandWeak) {
        if (simultaneousMode) {
          // In simultaneous mode, show if player hasn't decided yet
          return true; // Simplified for testing
        } else {
          // In sequential mode, show if it's player's turn
          return isMyDecision;
        }
      }
    }
    return false;
  };

  return (
    <>
      {/* Content section - shows dealing then weak hand alert */}
      <div {...stylex.props(styles.contentSection)}>
        {showDealing || isRedealing ? (
          /* Dealing animation */
          <div {...stylex.props(styles.dealingContainer)}>
            <div {...stylex.props(styles.dealingIcon)}>
              <div {...stylex.props(styles.cardStack, styles.cardStack1)} />
              <div {...stylex.props(styles.cardStack, styles.cardStack2)} />
              <div {...stylex.props(styles.cardStack, styles.cardStack3)} />
            </div>
            <div {...stylex.props(styles.dealingMessage)}>
              {isRedealing ? 'Redealing Cards' : 'Dealing Cards'}
            </div>
            <div {...stylex.props(styles.dealingStatus)}>
              Please wait while cards are being dealt...
            </div>

            <div {...stylex.props(styles.progressContainer)}>
              <div {...stylex.props(styles.progressBar)}>
                <div {...stylex.props(styles.progressFill)} />
              </div>
            </div>
          </div>
        ) : (
          <>
            {/* Weak hand alert - only show after dealing */}
            {shouldShowWeakHandAlert() && (
              <div {...stylex.props(
                styles.weakHandAlert,
                styles.weakHandAlertShow
              )}>
                <div {...stylex.props(styles.alertTitle)}>
                  ⚠️ Weak Hand Detected
                </div>
                <div {...stylex.props(styles.alertMessage)}>
                  No piece greater than {highestCardValue} points. Would you
                  like to request a redeal?
                  <div {...stylex.props(styles.multiplierWarning)}>
                    Warning: {redealMultiplier + 1}x penalty if you redeal!
                  </div>
                </div>
                <div {...stylex.props(styles.alertButtons)}>
                  <button
                    {...stylex.props(styles.alertButton, styles.primaryButton)}
                    onClick={onAcceptRedeal}
                  >
                    Request Redeal
                  </button>
                  <button
                    {...stylex.props(styles.alertButton, styles.secondaryButton)}
                    onClick={onDeclineRedeal}
                  >
                    Keep Hand
                  </button>
                </div>
              </div>
            )}

            {/* Simultaneous mode waiting indicator */}
            {simultaneousMode &&
              weakPlayersAwaiting.length > 0 &&
              !isMyDecision && (
                <div {...stylex.props(styles.waitingIndicator)}>
                  <div {...stylex.props(styles.waitingText)}>
                    Waiting for weak hand decisions...
                  </div>
                  <div {...stylex.props(styles.waitingProgress)}>
                    {decisionsReceived} of {decisionsNeeded} players decided
                  </div>
                </div>
              )}
          </>
        )}
      </div>

      {/* Hand section - ALWAYS visible at bottom like mockup */}
      <PieceTray
        key={`deal-${dealCount}`}
        pieces={myHand}
        variant="fixed"
        showValues
        animateAppear
        animationType="verticalDrop"
      />
    </>
  );
};

PreparationContent.propTypes = {
  myHand: PropTypes.array,
  players: PropTypes.array,
  weakHands: PropTypes.array,
  redealMultiplier: PropTypes.number,
  currentWeakPlayer: PropTypes.string,
  isMyDecision: PropTypes.bool,
  isMyHandWeak: PropTypes.bool,
  handValue: PropTypes.number,
  highestCardValue: PropTypes.number,
  simultaneousMode: PropTypes.bool,
  weakPlayersAwaiting: PropTypes.array,
  decisionsReceived: PropTypes.number,
  decisionsNeeded: PropTypes.number,
  dealingCards: PropTypes.bool,
  onAcceptRedeal: PropTypes.func,
  onDeclineRedeal: PropTypes.func,
};

export default PreparationContent;