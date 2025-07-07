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
  
  // Action props
  onAcceptRedeal,
  onDeclineRedeal
}) {
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
      onAcceptRedeal={onAcceptRedeal}
      onDeclineRedeal={onDeclineRedeal}
    />
  );
  
  // OLD TAILWIND UI BELOW - KEPT FOR REFERENCE
  const OLD_UI = (
    <div className="min-h-screen bg-gradient-to-br from-green-900 to-blue-900 p-4">
      <div className="max-w-6xl mx-auto">
        
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">
            🃏 Preparation Phase
          </h1>
          <p className="text-green-200 text-lg">
            {hasWeakHands 
              ? `Weak hands detected - Redeal decision needed`
              : `Cards dealt - Checking for weak hands...`
            }
          </p>
          
          {redealMultiplier > 1 && (
            <div className="mt-2 inline-block bg-yellow-500/20 border border-yellow-500/30 rounded-lg px-3 py-1">
              <span className="text-yellow-200 text-sm font-medium">
                Redeal Multiplier: {redealMultiplier}x
              </span>
            </div>
          )}
        </div>

        {/* Players Display */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-white mb-4 text-center">
            Players
          </h2>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {players.map((player) => (
              <PlayerSlot
                key={player.name}
                player={player}
                isActive={player.name === currentWeakPlayer}
                hasWeakHand={weakHands.includes(player.name)}
                className={`
                  ${weakHands.includes(player.name) ? 'ring-2 ring-yellow-400' : ''}
                  ${player.name === currentWeakPlayer ? 'ring-2 ring-blue-400 ring-offset-2' : ''}
                `}
              />
            ))}
          </div>
        </div>

        {/* My Hand */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-white mb-4 text-center">
            My Hand
            {isMyHandWeak && (
              <span className="ml-2 text-yellow-400 text-base">
                ⚠️ Weak Hand
              </span>
            )}
          </h2>
          
          {myHand.length > 0 ? (
            <div className="flex flex-wrap justify-center gap-2">
              {myHand.map((card, index) => (
                <GamePiece
                  key={`${card.suit}-${card.value}`}
                  card={card}
                  size="medium"
                  isHighlighted={isMyHandWeak}
                  className="transform hover:scale-105 transition-transform"
                />
              ))}
            </div>
          ) : (
            <div className="text-center text-gray-400 py-8">
              <div className="text-4xl mb-2">🃏</div>
              <p>Waiting for cards...</p>
            </div>
          )}
          
          {/* Hand Analysis */}
          {myHand.length > 0 && (
            <div className="mt-4 text-center text-sm text-green-200">
              <div>
                Hand Value: {handValue} points
              </div>
              <div>
                Highest Card: {highestCardValue} points
              </div>
              {isMyHandWeak && (
                <div className="text-yellow-300 font-medium">
                  ⚠️ Weak hand detected (no piece &gt; 9 points)
                </div>
              )}
            </div>
          )}
        </div>

        {/* Weak Hands Info */}
        {hasWeakHands && (
          <div className="mb-8">
            <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-yellow-200 mb-3 text-center">
                ⚠️ Weak Hands Detected
              </h3>
              
              <div className="text-yellow-100 text-center mb-4">
                Players with weak hands: {weakHands.join(', ')}
              </div>
              
              <div className="text-sm text-yellow-200 text-center">
                A weak hand has no cards worth more than 9 points.
                Players can request a redeal with a {redealMultiplier}x score multiplier.
              </div>
            </div>
          </div>
        )}

        {/* Decision Progress Indicator */}
        {simultaneousMode && weakHands.length > 0 && (
          <div className="mb-6 bg-blue-900/20 rounded-lg p-4">
            <div className="text-center mb-3">
              <div className="text-sm text-blue-200">
                Redeal Decisions: {decisionsReceived}/{decisionsNeeded}
              </div>
            </div>
            
            <div className="flex justify-center gap-2">
              {weakHands.map(player => {
                const hasDecided = !weakPlayersAwaiting.includes(player);
                return (
                  <div key={player} className={`
                    px-4 py-2 rounded-lg text-sm font-medium
                    ${hasDecided 
                      ? 'bg-green-600 text-white' 
                      : 'bg-yellow-600 text-yellow-100'}
                  `}>
                    {player} {hasDecided ? '✓' : '⏳'}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Redeal Decision Interface */}
        {((simultaneousMode && isMyDecision) || (!simultaneousMode && isWaitingForDecision)) && (
          <div className="mb-8">
            <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-blue-200 mb-4 text-center">
                Redeal Decision
              </h3>
              
              {isMyDecision ? (
                <div className="text-center">
                  <p className="text-blue-100 mb-6">
                    You have a weak hand. Do you want to request a redeal?
                  </p>
                  {simultaneousMode && (
                    <p className="text-sm text-blue-200 mb-4">
                      {decisionsReceived} of {decisionsNeeded} players have decided
                    </p>
                  )}
                  
                  <div className="flex justify-center gap-4">
                    <Button
                      onClick={onAcceptRedeal}
                      variant="success"
                      size="large"
                      className="px-8"
                      aria-label="Accept redeal"
                    >
                      ✅ Accept Redeal
                    </Button>
                    
                    <Button
                      onClick={onDeclineRedeal}
                      variant="secondary"
                      size="large"
                      className="px-8"
                      aria-label="Decline redeal"
                    >
                      ❌ Decline Redeal
                    </Button>
                  </div>
                  
                  <div className="mt-4 text-sm text-blue-200">
                    Accepting will trigger a redeal with {redealMultiplier}x score multiplier
                  </div>
                </div>
              ) : (
                <div className="text-center">
                  {simultaneousMode ? (
                    <p className="text-blue-100 mb-4">
                      Waiting for weak players to make their decisions...
                    </p>
                  ) : (
                    <p className="text-blue-100 mb-4">
                      Waiting for <span className="font-semibold text-blue-200">{currentWeakPlayer}</span> to decide on redeal...
                    </p>
                  )}
                  
                  <div className="flex justify-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400"></div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Status Footer */}
        <div className="text-center text-sm text-green-300">
          {!hasWeakHands && (
            <div>✅ No weak hands detected - Ready to proceed to Declaration phase</div>
          )}
          {hasWeakHands && !isWaitingForDecision && (
            <div>🔄 Processing weak hands...</div>
          )}
          {isWaitingForDecision && (
            <div>⏳ Waiting for redeal decision from {currentWeakPlayer}</div>
          )}
        </div>
      </div>
    </div>
  );
}

// No helper functions needed - all calculations done by backend

// PropTypes definition
PreparationUI.propTypes = {
  // Data props
  myHand: PropTypes.arrayOf(PropTypes.shape({
    type: PropTypes.string.isRequired,
    color: PropTypes.oneOf(['red', 'black']).isRequired,
    value: PropTypes.number.isRequired
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