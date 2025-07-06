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
import useGameState from "../../hooks/useGameState";
import useGameActions from "../../hooks/useGameActions";
import useConnectionStatus from "../../hooks/useConnectionStatus";

// Import Unified Game UI Component
import UnifiedGameUI from './UnifiedGameUI';
import WaitingUI from './WaitingUI';
import TurnResultsUI from './TurnResultsUI';
import ScoringUI from './ScoringUI';
import GameOverUI from './GameOverUI';
import ErrorBoundary from "../ErrorBoundary";

/**
 * Smart container that connects pure UI components to game state
 */
export function GameContainer({ roomId, onNavigateToLobby }) {
  const gameState = useGameState();
  const gameActions = useGameActions();
  const connectionStatus = useConnectionStatus(roomId);

  // Unified Game UI Props - handles all game phases
  const unifiedGameProps = useMemo(() => {
    // Map phase names
    const phaseMap = {
      'preparation': 'PREPARATION',
      'declaration': 'DECLARATION', 
      'turn': 'TURN',
      'scoring': 'SCORING'
    };
    
    const currentPhase = phaseMap[gameState.phase] || gameState.phase;
    
    // Common props for all phases
    const commonProps = {
      phase: currentPhase,
      myHand: gameState.myHand || [],
      players: (gameState.players || []).map(player => ({
        ...player,
        isMe: player.name === gameState.playerName
      })),
      roundNumber: gameState.currentRound || 1,
    };
    
    // Phase-specific props
    const phaseProps = {
      // Preparation phase
      weakHands: gameState.weakHands || [],
      redealMultiplier: gameState.redealMultiplier || 1,
      isMyHandWeak: gameState.isMyHandWeak || false,
      isMyDecision: gameState.isMyDecision || false,
      
      // Declaration phase
      declarations: gameState.declarations || {},
      currentTotal: gameState.currentTotal || 0,
      isMyTurnToDeclare: gameState.phase === 'declaration' && (gameState.isMyTurn || false),
      validOptions: gameState.validOptions || [],
      isLastPlayer: gameState.isLastPlayer || false,
      
      // Turn phase
      currentTurnPlays: gameState.currentTurnPlays || [],
      requiredPieceCount: gameState.requiredPieceCount,
      turnNumber: gameState.currentTurnNumber || 1,
      isMyTurn: gameState.phase === 'turn' && (gameState.isMyTurn || false),
      canPlayAnyCount: gameState.canPlayAnyCount || false,
      currentPlayer: gameState.currentPlayer || '',
      
      // Actions
      onAcceptRedeal: gameActions.acceptRedeal,
      onDeclineRedeal: gameActions.declineRedeal,
      onDeclare: gameActions.makeDeclaration,
      onPlayPieces: gameActions.playPieces
    };
    
    return { ...commonProps, ...phaseProps };
  }, [gameState, gameActions]);

  const turnResultsProps = useMemo(() => {
    if (gameState.phase !== 'turn_results') return null;
    
    console.log('🏆 GAMECONTAINER_DEBUG: Building turnResultsProps with gameState:');
    console.log('  🎮 gameState.phase:', gameState.phase);
    console.log('  🏅 gameState.turnWinner:', gameState.turnWinner);
    console.log('  🎯 gameState.winningPlay:', gameState.winningPlay);
    console.log('  📊 gameState.playerPiles:', gameState.playerPiles);
    console.log('  👥 gameState.players:', gameState.players);
    console.log('  🔢 gameState.turnNumber:', gameState.turnNumber);
    console.log('  🎪 gameState.nextStarter:', gameState.nextStarter);
    
    const props = {
      // Data from backend
      winner: gameState.turnWinner || null,
      winningPlay: gameState.winningPlay || null,
      playerPiles: gameState.playerPiles || {},
      players: gameState.players || [],
      turnNumber: gameState.turnNumber || 1,
      nextStarter: gameState.nextStarter || null
    };
    
    console.log('🏆 GAMECONTAINER_DEBUG: Final turnResultsProps:', props);
    return props;
  }, [gameState, gameActions]);

  const scoringProps = useMemo(() => {
    if (gameState.phase !== 'scoring') return null;
    
    const props = {
      // Data from backend (all calculated)
      players: gameState.players || [],
      roundScores: gameState.roundScores || {},
      totalScores: gameState.totalScores || {},
      redealMultiplier: gameState.redealMultiplier || 1,
      playersWithScores: gameState.playersWithScores || [], // backend provides sorted players with all score data
      
      // State from backend
      gameOver: gameState.gameOver || false,
      winners: gameState.winners || [],
      
      // Actions
      onStartNextRound: gameState.gameOver ? null : gameActions.startNextRound
    };
    
    console.log('🎮 GAME_CONTAINER_DEBUG: Passing props to ScoringUI:');
    console.log('  👥 players:', props.players);
    console.log('  📊 roundScores:', props.roundScores);
    console.log('  💯 totalScores:', props.totalScores);
    console.log('  🧮 playersWithScores:', props.playersWithScores);
    console.log('  ⚗️ redealMultiplier:', props.redealMultiplier);
    console.log('  🏁 gameOver:', props.gameOver);
    console.log('  🏆 winners:', props.winners);
    
    return props;
  }, [gameState, gameActions]);

  const waitingProps = useMemo(() => ({
    isConnected: connectionStatus.isConnected,
    isConnecting: connectionStatus.isConnecting,
    isReconnecting: connectionStatus.isReconnecting,
    connectionError: connectionStatus.error,
    message: getWaitingMessage(gameState, connectionStatus),
    phase: gameState.phase || 'waiting',
    onRetry: gameActions.triggerRecovery,
    onCancel: () => window.location.href = '/lobby'
  }), [gameState, connectionStatus, gameActions]);

  const gameOverProps = useMemo(() => {
    if (gameState.phase !== 'game_over') return null;
    
    return {
      finalRankings: gameState.final_rankings || [],
      gameStats: gameState.game_stats || { total_rounds: 0, game_duration: 'Unknown' },
      winners: gameState.winners || [],
      onBackToLobby: () => {
        // Clean up game state and navigate to lobby
        if (gameActions.cleanup) {
          gameActions.cleanup();
        }
        if (onNavigateToLobby) {
          onNavigateToLobby();
        }
      }
    };
  }, [gameState, gameActions, onNavigateToLobby]);

  // Error handling
  if (gameState.error) {
    return (
      <ErrorBoundary>
        <WaitingUI 
          {...waitingProps}
          message={`Error: ${gameState.error}`}
          connectionError={gameState.error}
        />
      </ErrorBoundary>
    );
  }

  // Connection handling
  if (!connectionStatus.isConnected && !connectionStatus.isConnecting) {
    return (
      <ErrorBoundary>
        <WaitingUI 
          {...waitingProps}
          message="Not connected to game"
        />
      </ErrorBoundary>
    );
  }

  // Loading states
  if (connectionStatus.isConnecting || connectionStatus.isReconnecting) {
    return (
      <ErrorBoundary>
        <WaitingUI 
          {...waitingProps}
          message={connectionStatus.isReconnecting ? "Reconnecting to game..." : "Connecting to game..."}
        />
      </ErrorBoundary>
    );
  }

  // Phase routing with error boundaries
  return (
    <ErrorBoundary>
      {(() => {
        switch (gameState.phase) {
          case 'preparation':
          case 'declaration':
          case 'turn':
            // Use UnifiedGameUI for main game phases
            return <UnifiedGameUI {...unifiedGameProps} />;
            
          case 'turn_results':
            console.log('🏆 GAMECONTAINER_DEBUG: Rendering TurnResultsUI with props:', turnResultsProps);
            return <TurnResultsUI {...turnResultsProps} />;
            
          case 'scoring':
            return <ScoringUI {...scoringProps} />;
            
          case 'game_over':
            return <GameOverUI {...gameOverProps} />;
            
          case 'waiting':
          default:
            return <WaitingUI {...waitingProps} />;
        }
      })()}
    </ErrorBoundary>
  );
}

// Helper functions
function getWaitingMessage(gameState, connectionStatus) {
  if (!connectionStatus.isConnected) {
    return "Connecting to game...";
  }
  
  if (connectionStatus.isReconnecting) {
    return "Reconnecting...";
  }
  
  switch (gameState.phase) {
    case 'waiting':
      return "Waiting for game to start...";
    case 'preparation':
      return "Preparing for next phase...";
    case 'declaration':
      return "Declaration phase in progress...";
    case 'turn':
      return "Turn phase in progress...";
    case 'turn_results':
      return "Showing turn results...";
    case 'scoring':
      return "Calculating scores...";
    default:
      return "Loading game...";
  }
}

// No business logic functions needed - all calculations done by backend

// PropTypes definition
GameContainer.propTypes = {
  roomId: PropTypes.string,
  onNavigateToLobby: PropTypes.func
};

GameContainer.defaultProps = {
  roomId: null,
  onNavigateToLobby: null
};

export default GameContainer;