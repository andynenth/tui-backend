import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { GamePiece } from '../shared';

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
  onAcceptRedeal,
  onDeclineRedeal
}) => {
  const [showDealing, setShowDealing] = useState(true);

  // Auto-hide dealing animation after 3.5s
  useEffect(() => {
    const timer = setTimeout(() => {
      setShowDealing(false);
    }, 3500);

    return () => clearTimeout(timer);
  }, []);

  // Check if we should show weak hand alert
  const shouldShowWeakHandAlert = () => {
    if (!showDealing) {
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
        {showDealing ? (
          /* Dealing animation */
          <div className="dealing-container">
            <div className="dealing-icon">
              <div className="card-stack"></div>
              <div className="card-stack"></div>
              <div className="card-stack"></div>
            </div>
            <div className="dealing-message">Dealing Cards</div>
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
                  {redealMultiplier > 1 && (
                    <div className="multiplier-warning">
                      Warning: {redealMultiplier}x penalty if you redeal!
                    </div>
                  )}
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
      <div className="hand-section">
        <div className="pieces-tray">
          {myHand.map((piece, index) => (
            <GamePiece
              key={index}
              piece={piece}
              size="large"
              showValue
              animationDelay={index * 0.1}
            />
          ))}
        </div>
      </div>
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
  onAcceptRedeal: PropTypes.func,
  onDeclineRedeal: PropTypes.func
};

export default PreparationContent;