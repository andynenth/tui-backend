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
 * ✅ Custom CSS styling
 */

import React from 'react';
import PropTypes from 'prop-types';
import PreparationContent from './content/PreparationContent';

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

  // Dealing animation flag
  dealingCards = false,

  // Action props
  onAcceptRedeal,
  onDeclineRedeal,
}) {
  // Debug log to check what data is received
  console.log('🎴 PreparationUI received myHand:', myHand);
  console.log('   myHand length:', myHand.length);
  console.log('   myHand data:', JSON.stringify(myHand));
  
  // Simply pass all props through to PreparationContent
  return (
    <PreparationContent
      myHand={myHand}
      players={players}
      weakHands={weakHands}
      redealMultiplier={redealMultiplier}
      currentWeakPlayer={currentWeakPlayer}
      isMyDecision={isMyDecision}
      isMyHandWeak={isMyHandWeak}
      handValue={handValue}
      highestCardValue={highestCardValue}
      simultaneousMode={simultaneousMode}
      weakPlayersAwaiting={weakPlayersAwaiting}
      decisionsReceived={decisionsReceived}
      decisionsNeeded={decisionsNeeded}
      dealingCards={dealingCards}
      onAcceptRedeal={onAcceptRedeal}
      onDeclineRedeal={onDeclineRedeal}
    />
  );
}

// No helper functions needed - all calculations done by backend

// PropTypes definition
PreparationUI.propTypes = {
  // Data props
  myHand: PropTypes.arrayOf(
    PropTypes.shape({
      kind: PropTypes.string.isRequired,
      color: PropTypes.oneOf(['red', 'black']).isRequired,
      value: PropTypes.number.isRequired,
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
  onAcceptRedeal: () => {},
  onDeclineRedeal: () => {},
};

export default PreparationUI;
