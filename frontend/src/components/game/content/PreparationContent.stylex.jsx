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
    padding: '1.5rem',
  },
  
  dealingContainer: {
    textAlign: 'center',
    animation: `${cardDeal} 0.5s 'cubic-bezier(0, 0, 0.2, 1)'`,
  },
  
  dealingIcon: {
    display: 'flex',
    justifyContent: 'center',
    gap: '0.25rem',
    marginBottom: '2rem',
  },
  
  cardStack: {
    width: '60px',
    height: '90px',
    backgroundColor: '#0d6efd',
    borderRadius: '0.375rem',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    position: 'relative',
    animation: `${cardDeal} 0.5s 'cubic-bezier(0, 0, 0.2, 1)'`,
    animationDelay: 'calc(var(--index) * 0.1s)',
    
    '::before': {
      content: '""',
      position: 'absolute',
      top: '-4px',
      left: '-4px',
      right: '4px',
      bottom: '4px',
      backgroundColor: '#e7f1ff',
      borderRadius: '0.375rem',
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
      borderRadius: '0.375rem',
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
    fontSize: '1.5rem',
    fontWeight: '700',
    color: '#343a40',
    marginBottom: '0.5rem',
  },
  
  dealingStatus: {
    fontSize: '1rem',
    color: '#6c757d',
    marginBottom: '2rem',
  },
  
  progressContainer: {
    width: '200px',
    height: '8px',
    backgroundColor: '#e9ecef',
    borderRadius: '9999px',
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
    borderRadius: '9999px',
    animation: `${progressFill} ${TIMING.DEALING_ANIMATION_DURATION}ms 'cubic-bezier(0.4, 0, 0.2, 1)'`,
  },
  
  weakHandAlert: {
    backgroundColor: '#ffffff',
    borderRadius: '0.5rem',
    padding: '2rem',
    boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    borderWidth: '2px',
    borderStyle: 'solid',
    borderColor: '#ffc107',
    maxWidth: '400px',
    margin: '0 auto',
    opacity: 0,
    transform: 'scale(0.9)',
    transition: `all '300ms' 'cubic-bezier(0, 0, 0.2, 1)'`,
  },
  
  weakHandAlertShow: {
    opacity: 1,
    transform: 'scale(1)',
  },
  
  alertTitle: {
    fontSize: '1.25rem',
    fontWeight: '700',
    color: '#ffc107',
    marginBottom: '1rem',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '0.5rem',
  },
  
  alertMessage: {
    fontSize: '1rem',
    color: '#495057',
    marginBottom: '1.5rem',
    lineHeight: 1.5,
  },
  
  multiplierWarning: {
    marginTop: '0.5rem',
    padding: '0.5rem',
    backgroundColor: 'rgba(245, 158, 11, 0.1)',
    borderRadius: '0.375rem',
    fontSize: '0.875rem',
    color: '#cc9a06',
    fontWeight: '500',
  },
  
  alertButtons: {
    display: 'flex',
    gap: '1rem',
    justifyContent: 'center',
  },
  
  alertButton: {
    padding: `'0.5rem' '1.5rem'`,
    borderRadius: '0.375rem',
    fontSize: '1rem',
    fontWeight: '500',
    border: 'none',
    cursor: 'pointer',
    transition: `all '300ms' 'cubic-bezier(0.4, 0, 0.2, 1)'`,
  },
  
  primaryButton: {
    background: gradients.primary,
    color: '#ffffff',
    
    ':hover': {
      transform: 'translateY(-2px)',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    },
  },
  
  secondaryButton: {
    backgroundColor: '#e9ecef',
    color: '#495057',
    
    ':hover': {
      backgroundColor: '#dee2e6',
    },
  },
  
  waitingIndicator: {
    textAlign: 'center',
    padding: '1.5rem',
    backgroundColor: '#f8f9fa',
    borderRadius: '0.375rem',
  },
  
  waitingText: {
    fontSize: '1.125rem',
    color: '#495057',
    marginBottom: '0.5rem',
  },
  
  waitingProgress: {
    fontSize: '0.875rem',
    color: '#6c757d',
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