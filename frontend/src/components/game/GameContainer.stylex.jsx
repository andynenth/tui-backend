/**
 * 🎮 **GameContainer Component** - Smart Container for Game State Management
 *
 * Phase 2, Task 2.3: Smart Container Components
 *
 * Features:
 * ✅ Connect pure UI components to game state
 * ✅ Handle all business logic and data transformation
 * ✅ Manage component lifecycle
 * ✅ Error boundary integration
 */

import React, { useMemo } from 'react';
import PropTypes from 'prop-types';
import useGameState from '../../hooks/useGameState';
import useGameActions from '../../hooks/useGameActions';
import useConnectionStatus from '../../hooks/useConnectionStatus';

// Import Pure UI Components (using StyleX versions where available)
import WaitingUI from './WaitingUI.stylex';
import PreparationUI from './PreparationUI.stylex';
import RoundStartUI from './RoundStartUI.stylex';
import DeclarationUI from './DeclarationUI';
import TurnUI from './TurnUI.stylex';
import TurnResultsUI from './TurnResultsUI';
import ScoringUI from './ScoringUI.stylex';
import GameOverUI from './GameOverUI.stylex';
import GameLayout from './GameLayout.stylex';
import ErrorBoundary from '../ErrorBoundary.stylex';

/**
 * Smart container that connects pure UI components to game state
 */
export function GameContainer({ roomId, onNavigateToLobby }) {
  const gameState = useGameState();
  const gameActions = useGameActions();
  const connectionStatus = useConnectionStatus(roomId);

  // Data transformation: Pass backend state to UI components (no business logic)
  const preparationProps = useMemo(() => {
    if (gameState.phase !== 'preparation') return null;

    return {
      // Data from backend
      myHand: gameState.myHand || [],
      players: gameState.players || [],
      weakHands: gameState.weakHands || [],
      redealMultiplier: gameState.redealMultiplier || 1,
      currentWeakPlayer: gameState.currentWeakPlayer,

      // State calculated by backend
      isMyDecision: gameState.isMyDecision || false,
      isMyHandWeak: gameState.isMyHandWeak || false,
      handValue: gameState.handValue || 0,
      highestCardValue: gameState.highestCardValue || 0,

      // Simultaneous mode props
      simultaneousMode: gameState.simultaneousMode || false,
      weakPlayersAwaiting: gameState.weakPlayersAwaiting || [],
      decisionsReceived: gameState.decisionsReceived || 0,
      decisionsNeeded: gameState.decisionsNeeded || 0,

      // Dealing animation flag
      dealingCards: gameState.dealingCards || false,

      // Actions
      onAcceptRedeal: gameActions.acceptRedeal,
      onDeclineRedeal: gameActions.declineRedeal,
    };
  }, [gameState, gameActions]);

  const roundStartProps = useMemo(() => {
    if (gameState.phase !== 'round_start') return null;

    return {
      // Data from backend
      roundNumber: gameState.currentRound || 1,
      starter: gameState.currentStarter || ',
      starterReason: gameState.starterReason || 'default',
    };
  }, [gameState]);

  const declarationProps = useMemo(() => {
    if (gameState.phase !== 'declaration') return null;

    // Order players based on declaration order from backend
    let orderedPlayers = gameState.players || [];
    if (gameState.declarationOrder && gameState.declarationOrder.length > 0) {
      // Map declaration order (player names) to player objects
      orderedPlayers = gameState.declarationOrder
        .map((playerName) => {
          // Find the full player object with is_bot property
          const fullPlayer = gameState.players.find(
            (p) => p.name === playerName
          );
          return fullPlayer || { name: playerName };
        })
        .filter((p) => p !== undefined);
    }

    // Get consecutive zeros for current player
    const currentPlayerData = gameState.players?.find(
      (p) => p.name === gameState.playerName
    );
    const consecutiveZeros = currentPlayerData?.zero_declares_in_a_row || 0;

    return {
      // Data from backend
      myHand: gameState.myHand || [],
      declarations: gameState.declarations || {},
      players: orderedPlayers,
      currentTotal: gameState.currentTotal || 0,
      currentPlayer: gameState.currentDeclarer || ',
      myName: gameState.playerName || ',

      // State calculated by backend
      isMyTurn: gameState.isMyTurn || false,
      validOptions: gameState.validOptions || [],
      declarationProgress: gameState.declarationProgress || {
        declared: 0,
        total: 4,
      },
      isLastPlayer: gameState.isLastPlayer || false,
      estimatedPiles: gameState.estimatedPiles || 0,
      handStrength: gameState.handStrength || 0,
      consecutiveZeros,
      redealMultiplier: gameState.redealMultiplier || 1,

      // Actions
      onDeclare: gameActions.makeDeclaration,
    };
  }, [gameState, gameActions]);

  const turnProps = useMemo(() => {
    if (gameState.phase !== 'turn') return null;

    // Extract play type from the starter's play
    let playType = ';
    if (
      gameState.currentTurnPlays &&
      gameState.currentTurnPlays.length > 0 &&
      gameState.currentTurnStarter
    ) {
      // Find the starter's play
      const starterPlay = gameState.currentTurnPlays.find(
        (play) => play.player === gameState.currentTurnStarter
      );

      if (starterPlay) {
        playType = starterPlay.play_type || ';
      }
    }

    return {
      // Data from backend
      myHand: gameState.myHand || [],
      currentPlayer: gameState.currentPlayer || ',
      turnNumber: gameState.turnNumber || 1,
      players: gameState.players || [],
      declarations: gameState.declarations || {},
      piles: gameState.piles || {},
      currentTurnPlays: gameState.currentTurnPlays || [],
      turnStarter: gameState.currentTurnStarter || ',
      requiredPieceCount: gameState.requiredPieceCount || 1,
      playType,
      selectedPieces: gameState.selectedPieces || [],
      myName: gameState.playerName || ',

      // State calculated by backend
      isMyTurn: gameState.isMyTurn || false,
      mustMatch: gameState.mustMatch || false,

      // Actions
      onSelectPiece: gameActions.togglePieceSelection,
      onPlayPieces: gameActions.playPieces,
      onClearSelection: gameActions.clearSelection,
    };
  }, [gameState, gameActions]);

  const turnResultsProps = useMemo(() => {
    if (gameState.phase !== 'turn_results') return null;

    return {
      // Data from backend
      turnNumber: gameState.turnNumber || 1,
      winner: gameState.lastTurnWinner || ',
      plays: gameState.lastTurnPlays || [],
      nextStarter: gameState.nextStarter || ',
    };
  }, [gameState]);

  const scoringProps = useMemo(() => {
    if (gameState.phase !== 'scoring') return null;

    return {
      // Data from backend
      players: gameState.players || [],
      declarations: gameState.declarations || {},
      piles: gameState.piles || {},
      scores: gameState.roundScores || {},
      multiplier: gameState.redealMultiplier || 1,
      currentRound: gameState.currentRound || 1,
    };
  }, [gameState]);

  const gameOverProps = useMemo(() => {
    if (gameState.phase !== 'game_over') return null;

    return {
      // Data from backend
      winner: gameState.winner || ',
      players: gameState.players || [],
      scores: gameState.finalScores || {},
      totalRounds: gameState.totalRounds || 1,

      // Actions
      onReturnToLobby: onNavigateToLobby,
    };
  }, [gameState, onNavigateToLobby]);

  // Render appropriate phase component within game layout
  const renderPhaseContent = () => {
    switch (gameState.phase) {
      case 'waiting':
        return <WaitingUI />;

      case 'preparation':
        return preparationProps ? (
          <PreparationUI {...preparationProps} />
        ) : null;

      case 'round_start':
        return roundStartProps ? (
          <RoundStartUI {...roundStartProps} />
        ) : null;

      case 'declaration':
        return declarationProps ? (
          <DeclarationUI {...declarationProps} />
        ) : null;

      case 'turn':
        return turnProps ? <TurnUI {...turnProps} /> : null;

      case 'turn_results':
        return turnResultsProps ? (
          <TurnResultsUI {...turnResultsProps} />
        ) : null;

      case 'scoring':
        return scoringProps ? <ScoringUI {...scoringProps} /> : null;

      case 'game_over':
        return gameOverProps ? <GameOverUI {...gameOverProps} /> : null;

      default:
        return <WaitingUI message={`Unknown phase: ${gameState.phase}`} />;
    }
  };

  return (
    <ErrorBoundary>
      <GameLayout
        currentPhase={gameState.phase}
        currentRound={gameState.currentRound}
        players={gameState.players || []}
        currentPlayer={gameState.currentPlayer}
        myName={gameState.playerName}
        connectionStatus={connectionStatus}
        onNavigateToLobby={onNavigateToLobby}
      >
        {renderPhaseContent()}
      </GameLayout>
    </ErrorBoundary>
  );
}

GameContainer.propTypes = {
  roomId: PropTypes.string.isRequired,
  onNavigateToLobby: PropTypes.func.isRequired,
};

export default GameContainer;