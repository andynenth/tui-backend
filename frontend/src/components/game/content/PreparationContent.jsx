import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { PieceTray } from '../shared';

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
  onDeclineRedeal
}) => {
  const [showDealing, setShowDealing] = useState(true);
  const [isRedealing, setIsRedealing] = useState(false);
  
  console.log(`🎴 DEBUG: PreparationContent - dealingCards=${dealingCards}, showDealing=${showDealing}, isRedealing=${isRedealing}`);
  
  // Track dealingCards prop changes
  useEffect(() => {
    console.log(`🎴 DEBUG: dealingCards prop changed to: ${dealingCards}`);
  }, [dealingCards]);

  // Track isMyHandWeak prop changes
  useEffect(() => {
    console.log(`🎴 DEBUG: isMyHandWeak prop changed to: ${isMyHandWeak}`);
    console.log(`🎴 DEBUG: Current state - showDealing=${showDealing}, isRedealing=${isRedealing}`);
  }, [isMyHandWeak]);

  // Auto-hide dealing animation after 3.5s
  useEffect(() => {
    console.log(`🎴 DEBUG: Initial dealing effect - setting timer to hide after 3.5s`);
    const timer = setTimeout(() => {
      console.log(`🎴 DEBUG: Initial dealing timer fired - setting showDealing=false`);
      setShowDealing(false);
    }, 3500);

    return () => {
      console.log(`🎴 DEBUG: Initial dealing effect cleanup`);
      clearTimeout(timer);
    };
  }, []);

  // Watch for redeal animation trigger
  useEffect(() => {
    console.log(`🎴 DEBUG: Redeal trigger effect - dealingCards=${dealingCards}, showDealing=${showDealing}, isRedealing=${isRedealing}`);
    
    if (dealingCards === true && !showDealing) {
      // Not initial deal, must be redeal!
      console.log(`🎴 DEBUG: Triggering redeal animation - setting isRedealing=true`);
      setIsRedealing(true);
    }
  }, [dealingCards, showDealing]);

  // Separate effect for redeal animation timer
  useEffect(() => {
    console.log(`🎴 DEBUG: Redeal timer effect - isRedealing=${isRedealing}`);
    
    if (isRedealing) {
      const timer = setTimeout(() => {
        console.log(`🎴 DEBUG: Redeal timer fired - setting isRedealing=false`);
        console.log(`🎴 DEBUG: After redeal animation - isMyHandWeak=${isMyHandWeak}, weakPlayersAwaiting=${JSON.stringify(weakPlayersAwaiting)}`);
        setIsRedealing(false);
      }, 3500);
      
      return () => {
        console.log(`🎴 DEBUG: Redeal timer cleanup`);
        clearTimeout(timer);
      };
    }
  }, [isRedealing, isMyHandWeak, weakPlayersAwaiting]);

  // Check if we should show weak hand alert
  const shouldShowWeakHandAlert = () => {
    const shouldShow = !showDealing && !isRedealing && isMyHandWeak;
    console.log(`🎴 DEBUG: shouldShowWeakHandAlert() called:
      - showDealing=${showDealing}
      - isRedealing=${isRedealing}
      - isMyHandWeak=${isMyHandWeak}
      - simultaneousMode=${simultaneousMode}
      - weakPlayersAwaiting=${JSON.stringify(weakPlayersAwaiting)}
      - decisionsReceived=${decisionsReceived}
      - decisionsNeeded=${decisionsNeeded}
      - RESULT=${shouldShow}`);
    
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
      <div className="content-section">
        {(showDealing || isRedealing) ? (
          /* Dealing animation */
          <div className="dealing-container">
            <div className="dealing-icon">
              <div className="card-stack"></div>
              <div className="card-stack"></div>
              <div className="card-stack"></div>
            </div>
            <div className="dealing-message">{isRedealing ? "Redealing Cards" : "Dealing Cards"}</div>
            <div className="dealing-status">Please wait while cards are being dealt...</div>
            
            <div className="progress-container">
              <div className="progress-bar">
                <div className="progress-fill"></div>
              </div>
            </div>
          </div>
        ) : (
          <>
            {/* Weak hand alert - only show after dealing */}
            {shouldShowWeakHandAlert() && (
              <div className="weak-hand-alert show">
                <div className="alert-title">
                  ⚠️ Weak Hand Detected
                </div>
                <div className="alert-message">
                  No piece greater than {highestCardValue} points. Would you like to request a redeal?
                  <div className="multiplier-warning">
                    Warning: {redealMultiplier + 1}x penalty if you redeal!
                  </div>
                </div>
                <div className="alert-buttons">
                  <button 
                    className="alert-button primary"
                    onClick={onAcceptRedeal}
                  >
                    Request Redeal
                  </button>
                  <button 
                    className="alert-button secondary"
                    onClick={onDeclineRedeal}
                  >
                    Keep Hand
                  </button>
                </div>
              </div>
            )}

            {/* Simultaneous mode waiting indicator */}
            {simultaneousMode && weakPlayersAwaiting.length > 0 && !isMyDecision && (
                <div className="waiting-indicator">
                  <div className="waiting-text">
                    Waiting for weak hand decisions...
                  </div>
                  <div className="waiting-progress">
                    {decisionsReceived} of {decisionsNeeded} players decided
                  </div>
                </div>
            )}
          </>
        )}
      </div>

      {/* Hand section - ALWAYS visible at bottom like mockup */}
      <PieceTray
        pieces={myHand}
        variant="fixed"
        showValues
        animateAppear
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
  onDeclineRedeal: PropTypes.func
};

export default PreparationContent;