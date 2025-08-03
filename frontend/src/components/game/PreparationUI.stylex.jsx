/**
 * 🃏 **PreparationUI Component** - Pure Preparation Phase Interface with StyleX
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

import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
import PieceTray from './shared/PieceTray.stylex';
import Button from '../Button.stylex';
import FooterTimer from './shared/FooterTimer.stylex';
import { TIMING } from '../../constants';
import { colors, spacing, shadows, layout, motion, typography } from '../../design-system/tokens.stylex';

// Animation keyframes
const dealingAnimation = stylex.keyframes({
  '0%': {
    transform: 'rotateY(0deg) translateZ(0)',
    opacity: 0,
  },
  '50%': {
    transform: 'rotateY(180deg) translateZ(50px)',
    opacity: 1,
  },
  '100%': {
    transform: 'rotateY(360deg) translateZ(0)',
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

const slideInUp = stylex.keyframes({
  '0%': {
    transform: 'translateY(100%)',
    opacity: 0,
  },
  '100%': {
    transform: 'translateY(0)',
    opacity: 1,
  },
});

const pulse = stylex.keyframes({
  '0%, 100%': {
    transform: 'scale(1)',
  },
  '50%': {
    transform: 'scale(1.05)',
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
  
  contentSection: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.lg,
  },
  
  // Dealing animation styles
  dealingContainer: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: spacing.lg,
    padding: spacing.xl,
    animation: `${slideInUp} ${motion.durationNormal} ${motion.easeOut}`,
  },
  
  dealingIcon: {
    position: 'relative',
    width: '120px',
    height: '120px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  
  cardStack: {
    position: 'absolute',
    width: '60px',
    height: '80px',
    backgroundColor: colors.primary,
    borderRadius: layout.radiusMd,
    boxShadow: shadows.lg,
    animation: `${dealingAnimation} 1.5s ${motion.easeInOut} infinite`,
  },
  
  cardStack1: {
    animationDelay: '0s',
    transform: 'translateX(-20px)',
  },
  
  cardStack2: {
    animationDelay: '0.3s',
    transform: 'translateX(0)',
  },
  
  cardStack3: {
    animationDelay: '0.6s',
    transform: 'translateX(20px)',
  },
  
  dealingMessage: {
    fontSize: typography.textXl,
    fontWeight: typography.weightBold,
    color: colors.textDark,
  },
  
  dealingStatus: {
    fontSize: typography.textMd,
    color: colors.gray600,
  },
  
  progressContainer: {
    width: '200px',
    height: '8px',
    backgroundColor: colors.gray200,
    borderRadius: layout.radiusFull,
    overflow: 'hidden',
  },
  
  progressBar: {
    height: '100%',
    backgroundColor: colors.primary,
    animation: `${progressFill} ${TIMING.DEALING_ANIMATION_DURATION}ms linear`,
  },
  
  // Weak hand alert styles
  weakHandAlert: {
    backgroundColor: colors.surface,
    border: `2px solid ${colors.warning}`,
    borderRadius: layout.radiusLg,
    padding: spacing.xl,
    maxWidth: '400px',
    boxShadow: shadows.xl,
    animation: `${slideInUp} ${motion.durationNormal} ${motion.easeOut}, ${pulse} 2s ${motion.easeInOut} infinite`,
  },
  
  alertTitle: {
    fontSize: typography.textLg,
    fontWeight: typography.weightBold,
    color: colors.warning,
    marginBottom: spacing.md,
    display: 'flex',
    alignItems: 'center',
    gap: spacing.sm,
  },
  
  alertMessage: {
    fontSize: typography.textMd,
    color: colors.textDark,
    marginBottom: spacing.lg,
    lineHeight: typography.lineHeightNormal,
  },
  
  multiplierWarning: {
    marginTop: spacing.sm,
    padding: spacing.sm,
    backgroundColor: 'rgba(255, 193, 7, 0.1)',
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
  
  // Simultaneous mode styles
  simultaneousWaiting: {
    backgroundColor: colors.surface,
    border: `1px solid ${colors.border}`,
    borderRadius: layout.radiusMd,
    padding: spacing.lg,
    textAlign: 'center',
  },
  
  simultaneousTitle: {
    fontSize: typography.textMd,
    fontWeight: typography.weightMedium,
    color: colors.textDark,
    marginBottom: spacing.sm,
  },
  
  simultaneousProgress: {
    fontSize: typography.textSm,
    color: colors.gray600,
    marginBottom: spacing.md,
  },
  
  simultaneousList: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: spacing.sm,
    justifyContent: 'center',
  },
  
  simultaneousPlayer: {
    padding: `${spacing.xs} ${spacing.sm}`,
    backgroundColor: colors.gray100,
    borderRadius: layout.radiusSm,
    fontSize: typography.textSm,
    color: colors.gray700,
  },
  
  // Hand tray section
  handTraySection: {
    position: 'sticky',
    bottom: 0,
    backgroundColor: colors.background,
    padding: spacing.md,
    borderTop: `1px solid ${colors.border}`,
    boxShadow: shadows.lg,
  },
  
  // Empty state
  emptyState: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: spacing.md,
    padding: spacing.xl,
    color: colors.gray500,
  },
  
  emptyIcon: {
    fontSize: '3rem',
    opacity: 0.5,
  },
  
  emptyText: {
    fontSize: typography.textMd,
  },
});

/**
 * Pure UI component for preparation phase with integrated content
 */
export function PreparationUI({
  // Data props
  myHand = [],
  players = [],
  weakHands = [],
  redealMultiplier = 1,
  
  // State props (calculated by backend)
  currentWeakPlayer = null,
  isMyDecision = false,
  isMyHandWeak = false,
  handValue = 0,
  highestCardValue = 0,
  
  // Simultaneous mode props
  simultaneousMode = false,
  weakPlayersAwaiting = [],
  decisionsReceived = 0,
  decisionsNeeded = 0,
  
  // Dealing animation flag
  dealingCards = false,
  
  // Action props
  onAcceptRedeal,
  onDeclineRedeal,
  
  // Additional props
  className = '',
}) {
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
  }, [isRedealing]);
  
  // Check if we should show weak hand alert
  const shouldShowWeakHandAlert = () => {
    if (!showDealing && !isRedealing && isMyHandWeak) {
      if (simultaneousMode) {
        // In simultaneous mode, show if player hasn't decided yet
        return true;
      } else {
        // In sequential mode, show if it's player's turn
        return isMyDecision;
      }
    }
    return false;
  };
  
  return (
    <div {...stylex.props(styles.container, className && { className })}>
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
              <div {...stylex.props(styles.progressBar)} />
            </div>
          </div>
        ) : (
          <>
            {/* Weak hand alert - only show after dealing */}
            {shouldShowWeakHandAlert() && (
              <div {...stylex.props(styles.weakHandAlert)}>
                <div {...stylex.props(styles.alertTitle)}>
                  <span>⚠️</span>
                  <span>Weak Hand Detected</span>
                </div>
                <div {...stylex.props(styles.alertMessage)}>
                  No piece greater than {highestCardValue} points. Would you
                  like to request a redeal?
                  <div {...stylex.props(styles.multiplierWarning)}>
                    Warning: {redealMultiplier + 1}x penalty if you redeal!
                  </div>
                </div>
                <div {...stylex.props(styles.alertButtons)}>
                  <Button
                    onClick={onAcceptRedeal}
                    variant="primary"
                  >
                    Request Redeal
                  </Button>
                  <Button
                    onClick={onDeclineRedeal}
                    variant="secondary"
                  >
                    Keep Hand
                  </Button>
                </div>
              </div>
            )}
            
            {/* Simultaneous mode waiting indicator */}
            {simultaneousMode && !shouldShowWeakHandAlert() && weakPlayersAwaiting.length > 0 && (
              <div {...stylex.props(styles.simultaneousWaiting)}>
                <div {...stylex.props(styles.simultaneousTitle)}>
                  Waiting for weak hand decisions...
                </div>
                <div {...stylex.props(styles.simultaneousProgress)}>
                  {decisionsReceived} of {decisionsNeeded} decisions received
                </div>
                <div {...stylex.props(styles.simultaneousList)}>
                  {weakPlayersAwaiting.map((player) => (
                    <div key={player} {...stylex.props(styles.simultaneousPlayer)}>
                      {player}
                    </div>
                  ))}
                </div>
                <FooterTimer
                  duration={15}
                  prefix="Time remaining:"
                  variant="inline"
                  size="small"
                />
              </div>
            )}
            
            {/* Empty state when nothing to show */}
            {!shouldShowWeakHandAlert() && !simultaneousMode && (
              <div {...stylex.props(styles.emptyState)}>
                <div {...stylex.props(styles.emptyIcon)}>🃏</div>
                <div {...stylex.props(styles.emptyText)}>
                  Cards dealt successfully
                </div>
              </div>
            )}
          </>
        )}
      </div>
      
      {/* Player's hand tray - always visible at bottom */}
      <div {...stylex.props(styles.handTraySection)}>
        <PieceTray
          key={`hand-${dealCount}`} // Force re-render on redeal
          pieces={myHand}
          variant="fixed"
          showValues={true}
          animateAppear={showDealing || isRedealing}
          animationType="verticalDrop"
          label="Your Hand"
        />
      </div>
    </div>
  );
}

// PropTypes definition
PreparationUI.propTypes = {
  // Data props
  myHand: PropTypes.arrayOf(
    PropTypes.shape({
      type: PropTypes.string,
      kind: PropTypes.string,
      color: PropTypes.string,
      value: PropTypes.number,
    })
  ),
  players: PropTypes.arrayOf(
    PropTypes.shape({
      name: PropTypes.string.isRequired,
      isActive: PropTypes.bool,
    })
  ).isRequired,
  weakHands: PropTypes.arrayOf(PropTypes.string),
  redealMultiplier: PropTypes.number,
  
  // State props (calculated by backend)
  currentWeakPlayer: PropTypes.string,
  isMyDecision: PropTypes.bool.isRequired,
  isMyHandWeak: PropTypes.bool,
  handValue: PropTypes.number,
  highestCardValue: PropTypes.number,
  
  // Simultaneous mode props
  simultaneousMode: PropTypes.bool,
  weakPlayersAwaiting: PropTypes.arrayOf(PropTypes.string),
  decisionsReceived: PropTypes.number,
  decisionsNeeded: PropTypes.number,
  
  // Dealing animation flag
  dealingCards: PropTypes.bool,
  
  // Action props
  onAcceptRedeal: PropTypes.func,
  onDeclineRedeal: PropTypes.func,
  
  // Additional props
  className: PropTypes.string,
};

PreparationUI.defaultProps = {
  myHand: [],
  weakHands: [],
  redealMultiplier: 1,
  currentWeakPlayer: null,
  isMyHandWeak: false,
  handValue: 0,
  highestCardValue: 0,
  simultaneousMode: false,
  weakPlayersAwaiting: [],
  decisionsReceived: 0,
  decisionsNeeded: 0,
  dealingCards: false,
  onAcceptRedeal: null,
  onDeclineRedeal: null,
  className: '',
};

export default PreparationUI;