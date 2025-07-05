/**
 * 🃏 **PreparationUI Component** - Pure Preparation Phase Interface
 * 
 * Phase 2, Task 2.2: Pure UI Components
 * 
 * Features:
 * ✅ Pure functional component (props in, JSX out)
 * ✅ No hooks except local UI state
 * ✅ Comprehensive prop interfaces
 * ✅ Accessible and semantic HTML
 * ✅ Tailwind CSS styling
 */

import React from 'react';
import PropTypes from 'prop-types';
import Button from "../Button";
import { GamePhaseContainer, PhaseHeader, HandSection } from '../shared';

/**
 * Pure UI component for preparation phase
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
  
  // Action props
  onAcceptRedeal,
  onDeclineRedeal
}) {
  const hasWeakHands = weakHands.length > 0;
  const isWaitingForDecision = hasWeakHands && currentWeakPlayer !== null;

  return (
    <GamePhaseContainer phase="preparation">
      <PhaseHeader 
        title="Preparation" 
        subtitle="Dealing Cards"
        roundNumber={1}
      />

      {/* Dealing Animation Section */}
      <div className="px-5 py-8 flex-1 flex flex-col justify-center">
        {!hasWeakHands ? (
          <div className="text-center">
            {/* Dealing Animation */}
            <div className="mb-6">
              <div className="flex justify-center mb-4">
                {Array.from({ length: 6 }).map((_, index) => (
                  <div
                    key={index}
                    className="w-12 h-12 bg-gradient-to-br from-white to-gray-100 rounded-lg border-2 border-gray-300 shadow-md mx-1 animate-pulse"
                    style={{
                      animationDelay: `${index * 0.2}s`,
                      animationDuration: '1.5s'
                    }}
                  ></div>
                ))}
              </div>
              <div className="text-gray-600 font-medium mb-2">Dealing cards...</div>
              <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
                <div className="bg-blue-500 h-2 rounded-full animate-pulse" style={{ width: '75%' }}></div>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-yellow-50 border border-yellow-200 rounded-2xl p-6 mb-4">
            <div className="text-center">
              <div className="text-3xl mb-4">⚠️</div>
              <h3 className="text-lg font-semibold text-yellow-700 mb-2">
                Weak Hands Detected
              </h3>
              <p className="text-yellow-600 text-sm mb-4">
                Players with weak hands: {weakHands.join(', ')}
              </p>
              
              {redealMultiplier > 1 && (
                <div className="bg-yellow-100 border border-yellow-300 rounded-lg px-3 py-2 inline-block">
                  <span className="text-yellow-700 text-sm font-medium">
                    Redeal Multiplier: {redealMultiplier}x
                  </span>
                </div>
              )}
            </div>
            
            {/* Redeal Decision Interface */}
            {isMyDecision && (
              <div className="mt-6 text-center">
                <p className="text-yellow-700 mb-4">
                  You have a weak hand. Do you want to request a redeal?
                </p>
                
                <div className="flex justify-center gap-3">
                  <Button
                    onClick={onAcceptRedeal}
                    variant="success"
                    size="medium"
                    className="px-6"
                  >
                    ✅ Accept Redeal
                  </Button>
                  
                  <Button
                    onClick={onDeclineRedeal}
                    variant="secondary"
                    size="medium"
                    className="px-6"
                  >
                    ❌ Decline
                  </Button>
                </div>
              </div>
            )}
            
            {!isMyDecision && currentWeakPlayer && (
              <div className="mt-4 text-center">
                <p className="text-yellow-600 text-sm">
                  Waiting for {currentWeakPlayer} to decide...
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Hand Section */}
      <HandSection 
        pieces={myHand}
        isActivePlayer={isMyHandWeak}
        disabled={true}
        title={isMyHandWeak ? "Your Hand ⚠️ Weak Hand" : null}
      />
    </GamePhaseContainer>
  );
}

// No helper functions needed - all calculations done by backend

// PropTypes definition
PreparationUI.propTypes = {
  // Data props
  myHand: PropTypes.arrayOf(PropTypes.shape({
    suit: PropTypes.string.isRequired,
    value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired
  })),
  players: PropTypes.arrayOf(PropTypes.shape({
    name: PropTypes.string.isRequired,
    isActive: PropTypes.bool
  })).isRequired,
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
  
  // Action props
  onAcceptRedeal: PropTypes.func,
  onDeclineRedeal: PropTypes.func
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
  onAcceptRedeal: () => {},
  onDeclineRedeal: () => {}
};

export default PreparationUI;