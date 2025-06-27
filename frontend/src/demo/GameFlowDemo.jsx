/**
 * 🎮 **Game Flow Demo** - Complete UI Mockup with Realistic Data
 * 
 * Demonstrates the entire game flow from preparation to end game
 * including redeal requests, multiple turns, and scoring phases.
 */

import React, { useState } from 'react';
import PreparationUI from '../components/game/PreparationUI';
import DeclarationUI from '../components/game/DeclarationUI';
import TurnUI from '../components/game/TurnUI';
import TurnResultsUI from '../components/game/TurnResultsUI';
import ScoringUI from '../components/game/ScoringUI';
import Button from '../components/Button';

// Mock realistic game data
const DEMO_DATA = {
  players: [
    { name: "Alice", is_bot: false, zero_declares_in_a_row: 0 },
    { name: "Bot_Charlie", is_bot: true, zero_declares_in_a_row: 1 },
    { name: "Bot_David", is_bot: true, zero_declares_in_a_row: 0 },
    { name: "Bot_Eve", is_bot: true, zero_declares_in_a_row: 0 }
  ],

  // Realistic hand with weak cards (no card > 9 points)
  weakHand: [
    { color: "red", point: 2, kind: "number" },
    { color: "black", point: 3, kind: "number" },
    { color: "red", point: 5, kind: "number" },
    { color: "black", point: 4, kind: "number" },
    { color: "red", point: 6, kind: "number" },
    { color: "black", point: 7, kind: "number" },
    { color: "red", point: 8, kind: "number" },
    { color: "black", point: 9, kind: "number" }
  ],

  // Strong hand after redeal
  strongHand: [
    { color: "red", point: 13, kind: "king" },
    { color: "black", point: 12, kind: "queen" },
    { color: "red", point: 11, kind: "jack" },
    { color: "black", point: 10, kind: "number" },
    { color: "red", point: 9, kind: "number" },
    { color: "black", point: 8, kind: "number" },
    { color: "red", point: 7, kind: "number" },
    { color: "black", point: 6, kind: "number" }
  ],

  // Turn playing hand (after some cards played)
  turnHand: [
    { color: "red", point: 13, kind: "king" },
    { color: "black", point: 12, kind: "queen" },
    { color: "red", point: 11, kind: "jack" },
    { color: "black", point: 10, kind: "number" },
    { color: "red", point: 9, kind: "number" }
  ],

  // Current turn plays
  currentTurnPlays: [
    {
      player: "Alice",
      cards: [
        { color: "red", point: 13, kind: "king" },
        { color: "black", point: 12, kind: "queen" },
        { color: "red", point: 11, kind: "jack" }
      ],
      isValid: true,
      playType: "Straight",
      totalValue: 36
    },
    {
      player: "Bot_Charlie",
      cards: [
        { color: "black", point: 10, kind: "number" },
        { color: "red", point: 9, kind: "number" },
        { color: "black", point: 8, kind: "number" }
      ],
      isValid: true,
      playType: "Straight",
      totalValue: 27
    },
    {
      player: "Bot_David",
      cards: [
        { color: "red", point: 7, kind: "number" },
        { color: "black", point: 6, kind: "number" },
        { color: "red", point: 5, kind: "number" }
      ],
      isValid: true,
      playType: "Straight",
      totalValue: 18
    }
  ],

  // Declarations data
  declarations: {
    "Alice": 3,
    "Bot_Charlie": 1,
    "Bot_David": 2
  },

  // Player pile counts throughout the game
  playerPiles: {
    "Alice": 7,
    "Bot_Charlie": 4,
    "Bot_David": 6,
    "Bot_Eve": 3
  },

  // Final scores
  finalScores: {
    "Alice": 42,
    "Bot_Charlie": 28,
    "Bot_David": 35,
    "Bot_Eve": 18
  }
};

const GAME_PHASES = [
  'preparation_weak',
  'preparation_redeal_decision',
  'preparation_redealt',
  'declaration_start',
  'declaration_progress',
  'declaration_complete',
  'turn_start',
  'turn_in_progress',
  'turn_waiting',
  'turn_results',
  'turn_multiple',
  'scoring_round',
  'scoring_final'
];

export function GameFlowDemo() {
  const [currentPhase, setCurrentPhase] = useState(0);
  const [autoPlay, setAutoPlay] = useState(false);

  const getCurrentPhase = () => GAME_PHASES[currentPhase];
  
  const nextPhase = () => {
    if (currentPhase < GAME_PHASES.length - 1) {
      setCurrentPhase(currentPhase + 1);
    }
  };

  const prevPhase = () => {
    if (currentPhase > 0) {
      setCurrentPhase(currentPhase - 1);
    }
  };

  const jumpToPhase = (index) => {
    setCurrentPhase(index);
  };

  // Auto-advance through phases
  React.useEffect(() => {
    if (autoPlay) {
      const timer = setTimeout(() => {
        nextPhase();
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [currentPhase, autoPlay]);

  const renderCurrentPhase = () => {
    const phase = getCurrentPhase();
    
    switch (phase) {
      case 'preparation_weak':
        return (
          <PreparationUI
            myHand={DEMO_DATA.weakHand}
            players={DEMO_DATA.players}
            weakHands={["Alice"]}
            redealMultiplier={1}
            currentWeakPlayer="Alice"
            isMyDecision={true}
            isMyHandWeak={true}
            handValue={44} // Sum of weak hand
            highestCardValue={9}
            onAcceptRedeal={() => nextPhase()}
            onDeclineRedeal={() => jumpToPhase(3)} // Skip to declaration
          />
        );

      case 'preparation_redeal_decision':
        return (
          <div className="min-h-screen bg-gradient-to-br from-orange-900 to-red-900 p-4 flex items-center justify-center">
            <div className="bg-white/10 backdrop-blur-md rounded-xl p-8 text-center max-w-md">
              <div className="text-6xl mb-4">🔄</div>
              <h2 className="text-2xl font-bold text-white mb-4">Redeal Requested</h2>
              <p className="text-orange-200 mb-6">
                Alice has requested a redeal due to weak hand (no cards {'>'} 9 points).
                Shuffling and dealing new cards...
              </p>
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-400 mx-auto mb-4"></div>
              <Button onClick={nextPhase} variant="primary">
                Continue to New Hand
              </Button>
            </div>
          </div>
        );

      case 'preparation_redealt':
        return (
          <PreparationUI
            myHand={DEMO_DATA.strongHand}
            players={DEMO_DATA.players}
            weakHands={[]}
            redealMultiplier={2} // Doubled due to redeal
            currentWeakPlayer={null}
            isMyDecision={false}
            isMyHandWeak={false}
            handValue={76} // Sum of strong hand
            highestCardValue={13}
            onAcceptRedeal={() => {}}
            onDeclineRedeal={() => {}}
          />
        );

      case 'declaration_start':
        return (
          <DeclarationUI
            myHand={DEMO_DATA.strongHand}
            declarations={{}}
            players={DEMO_DATA.players}
            currentTotal={0}
            isMyTurn={true}
            validOptions={[0, 1, 2, 3, 4, 5, 6, 7, 8]}
            declarationProgress={{ declared: 0, total: 4 }}
            isLastPlayer={false}
            estimatedPiles={3}
            handStrength={85}
            onDeclare={(value) => nextPhase()}
          />
        );

      case 'declaration_progress':
        return (
          <DeclarationUI
            myHand={DEMO_DATA.strongHand}
            declarations={DEMO_DATA.declarations}
            players={DEMO_DATA.players}
            currentTotal={6} // 3 + 1 + 2
            isMyTurn={false}
            validOptions={[]}
            declarationProgress={{ declared: 3, total: 4 }}
            isLastPlayer={false}
            estimatedPiles={3}
            handStrength={85}
            onDeclare={() => {}}
          />
        );

      case 'declaration_complete':
        return (
          <DeclarationUI
            myHand={DEMO_DATA.strongHand}
            declarations={{ ...DEMO_DATA.declarations, "Bot_Eve": 1 }} // Total = 7 (not 8)
            players={DEMO_DATA.players}
            currentTotal={7}
            isMyTurn={false}
            validOptions={[]}
            declarationProgress={{ declared: 4, total: 4 }}
            isLastPlayer={false}
            estimatedPiles={3}
            handStrength={85}
            onDeclare={() => {}}
          />
        );

      case 'turn_start':
        return (
          <TurnUI
            myHand={DEMO_DATA.strongHand}
            currentTurnPlays={[]}
            requiredPieceCount={null}
            turnNumber={1}
            isMyTurn={true}
            canPlayAnyCount={true} // First player
            selectedPlayValue={0}
            onPlayPieces={() => nextPhase()}
          />
        );

      case 'turn_in_progress':
        return (
          <TurnUI
            myHand={DEMO_DATA.turnHand}
            currentTurnPlays={DEMO_DATA.currentTurnPlays}
            requiredPieceCount={3}
            turnNumber={1}
            isMyTurn={false}
            canPlayAnyCount={false}
            selectedPlayValue={0}
            onPlayPieces={() => {}}
          />
        );

      case 'turn_waiting':
        return (
          <TurnUI
            myHand={DEMO_DATA.turnHand}
            currentTurnPlays={[
              ...DEMO_DATA.currentTurnPlays,
              {
                player: "Bot_Eve",
                cards: [
                  { color: "black", point: 4, kind: "number" },
                  { color: "red", point: 3, kind: "number" },
                  { color: "black", point: 2, kind: "number" }
                ],
                isValid: true,
                playType: "Straight",
                totalValue: 9
              }
            ]}
            requiredPieceCount={3}
            turnNumber={1}
            isMyTurn={false}
            canPlayAnyCount={false}
            selectedPlayValue={0}
            onPlayPieces={() => {}}
          />
        );

      case 'turn_results':
        return (
          <TurnResultsUI
            winner="Alice"
            winningPlay={{
              pieces: ["King♥", "Queen♠", "Jack♥"],
              value: 36,
              type: "Straight",
              pilesWon: 3
            }}
            playerPiles={{
              "Alice": 3,
              "Bot_Charlie": 0,
              "Bot_David": 0,
              "Bot_Eve": 0
            }}
            players={DEMO_DATA.players}
            turnNumber={1}
            nextStarter="Alice"
            onContinueToNextTurn={nextPhase}
          />
        );

      case 'turn_multiple':
        return (
          <TurnResultsUI
            winner="Bot_David"
            winningPlay={{
              pieces: ["10♠", "9♥"],
              value: 19,
              type: "Pair",
              pilesWon: 2
            }}
            playerPiles={DEMO_DATA.playerPiles}
            players={DEMO_DATA.players}
            turnNumber={8}
            nextStarter="Bot_David"
            onContinueToNextTurn={nextPhase}
          />
        );

      case 'scoring_round':
        return (
          <ScoringUI
            players={DEMO_DATA.players}
            roundScores={{
              "Alice": 12, // 3 declared, 7 actual, difference 4, multiplied by redeal multiplier 2 + bonus
              "Bot_Charlie": 6,
              "Bot_David": 8,
              "Bot_Eve": 4
            }}
            totalScores={{
              "Alice": 28,
              "Bot_Charlie": 15,
              "Bot_David": 20,
              "Bot_Eve": 12
            }}
            redealMultiplier={2}
            playersWithScores={[
              { 
                ...DEMO_DATA.players[0], 
                actualPiles: 7, 
                declaredPiles: 3, 
                difference: 4, 
                roundScore: 12, 
                totalScore: 28 
              },
              { 
                ...DEMO_DATA.players[1], 
                actualPiles: 4, 
                declaredPiles: 1, 
                difference: 3, 
                roundScore: 6, 
                totalScore: 15 
              },
              { 
                ...DEMO_DATA.players[2], 
                actualPiles: 6, 
                declaredPiles: 2, 
                difference: 4, 
                roundScore: 8, 
                totalScore: 20 
              },
              { 
                ...DEMO_DATA.players[3], 
                actualPiles: 3, 
                declaredPiles: 1, 
                difference: 2, 
                roundScore: 4, 
                totalScore: 12 
              }
            ]}
            gameOver={false}
            winners={[]}
            onStartNextRound={nextPhase}
            onEndGame={() => {}}
          />
        );

      case 'scoring_final':
        return (
          <ScoringUI
            players={DEMO_DATA.players}
            roundScores={{
              "Alice": 14,
              "Bot_Charlie": 13,
              "Bot_David": 15,
              "Bot_Eve": 6
            }}
            totalScores={DEMO_DATA.finalScores}
            redealMultiplier={1}
            playersWithScores={[
              { 
                ...DEMO_DATA.players[0], 
                actualPiles: 5, 
                declaredPiles: 4, 
                difference: 1, 
                roundScore: 14, 
                totalScore: 42,
                isWinner: true
              },
              { 
                ...DEMO_DATA.players[2], 
                actualPiles: 7, 
                declaredPiles: 2, 
                difference: 5, 
                roundScore: 15, 
                totalScore: 35 
              },
              { 
                ...DEMO_DATA.players[1], 
                actualPiles: 0, 
                declaredPiles: 2, 
                difference: 2, 
                roundScore: 13, 
                totalScore: 28 
              },
              { 
                ...DEMO_DATA.players[3], 
                actualPiles: 8, 
                declaredPiles: 0, 
                difference: 8, 
                roundScore: 6, 
                totalScore: 18 
              }
            ]}
            gameOver={true}
            winners={["Alice"]}
            onStartNextRound={() => {}}
            onEndGame={() => alert("Game completed! Alice wins with 42 points.")}
          />
        );

      default:
        return <div>Unknown phase</div>;
    }
  };

  return (
    <div className="min-h-screen">
      {/* Demo Controls */}
      <div className="fixed top-4 left-4 z-50 bg-gray-900/90 backdrop-blur-md rounded-lg p-4 text-white max-w-sm">
        <h3 className="font-bold mb-2">🎮 Game Flow Demo</h3>
        <div className="text-sm mb-3">
          <div>Phase: <span className="font-mono text-green-400">{currentPhase + 1}/{GAME_PHASES.length}</span></div>
          <div>Current: <span className="text-blue-400">{getCurrentPhase()}</span></div>
        </div>
        
        <div className="flex gap-2 mb-3">
          <Button 
            onClick={prevPhase} 
            disabled={currentPhase === 0}
            size="small"
            variant="secondary"
          >
            ← Prev
          </Button>
          <Button 
            onClick={nextPhase} 
            disabled={currentPhase === GAME_PHASES.length - 1}
            size="small"
            variant="primary"
          >
            Next →
          </Button>
        </div>

        <div className="mb-3">
          <label className="flex items-center gap-2 text-sm">
            <input 
              type="checkbox" 
              checked={autoPlay}
              onChange={(e) => setAutoPlay(e.target.checked)}
              className="rounded"
            />
            Auto-advance (3s)
          </label>
        </div>

        {/* Phase Navigation */}
        <div className="text-xs">
          <div className="mb-2 font-semibold">Quick Jump:</div>
          <div className="grid grid-cols-2 gap-1">
            {GAME_PHASES.map((phase, index) => (
              <button
                key={phase}
                onClick={() => jumpToPhase(index)}
                className={`text-left px-2 py-1 rounded text-xs ${
                  index === currentPhase 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                }`}
              >
                {phase.replace(/_/g, ' ')}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Phase Content */}
      <div className="demo-content">
        {renderCurrentPhase()}
      </div>

      {/* Phase Description */}
      <div className="fixed bottom-4 right-4 z-50 bg-gray-900/90 backdrop-blur-md rounded-lg p-4 text-white max-w-md">
        <h4 className="font-bold mb-2">📝 Phase Description</h4>
        <div className="text-sm">
          {getPhaseDescription(getCurrentPhase())}
        </div>
      </div>
    </div>
  );
}

function getPhaseDescription(phase) {
  const descriptions = {
    'preparation_weak': 'Alice receives a weak hand (no cards greater than 9 points) and must decide whether to request a redeal.',
    'preparation_redeal_decision': 'System processes the redeal request and shuffles new cards.',
    'preparation_redealt': 'Alice receives a strong new hand. Redeal multiplier is now 2x for scoring.',
    'declaration_start': 'Declaration phase begins. Alice (with strong hand) declares target pile count.',
    'declaration_progress': 'Other players make their declarations. Total cannot equal 8.',
    'declaration_complete': 'All players have declared. Total is 7 (valid). Ready for turn phase.',
    'turn_start': 'Turn phase begins. Alice starts first and can play 1-6 pieces to set the turn requirement.',
    'turn_in_progress': 'Players take turns playing pieces. Must match starter\'s piece count (3 pieces).',
    'turn_waiting': 'All players have played. Alice wins with highest straight (K-Q-J = 36 points).',
    'turn_results': 'Turn results show Alice as winner, earning 3 piles. Next turn will start with Alice.',
    'turn_multiple': 'Multiple turns later (Turn 8), Bot_David wins with a pair. Pile counts have accumulated.',
    'scoring_round': 'Round 1 scoring: Compare declared vs actual piles. Alice gets bonus for accuracy.',
    'scoring_final': 'Final game results: Alice wins with 42 points after multiple rounds!'
  };
  
  return descriptions[phase] || 'Unknown phase';
}

export default GameFlowDemo;