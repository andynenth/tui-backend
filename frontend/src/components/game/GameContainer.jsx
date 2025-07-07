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
// Play type detection now handled by backend

// Import Pure UI Components
import WaitingUI from './WaitingUI';
import PreparationUI from './PreparationUI';
import DeclarationUI from './DeclarationUI';
import TurnUI from './TurnUI';
import TurnResultsUI from './TurnResultsUI';
import ScoringUI from './ScoringUI';
import GameOverUI from './GameOverUI';
import GameLayout from './GameLayout';
import ErrorBoundary from "../ErrorBoundary";

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
      
      // Actions
      onAcceptRedeal: gameActions.acceptRedeal,
      onDeclineRedeal: gameActions.declineRedeal
    };
  }, [gameState, gameActions]);

  const declarationProps = useMemo(() => {
    if (gameState.phase !== 'declaration') return null;
    
    return {
      // Data from backend
      myHand: gameState.myHand || [],
      declarations: gameState.declarations || {},
      players: gameState.players || [],
      currentTotal: gameState.currentTotal || 0,
      
      // State calculated by backend
      isMyTurn: gameState.isMyTurn || false,
      validOptions: gameState.validOptions || [],
      declarationProgress: gameState.declarationProgress || { declared: 0, total: 4 },
      isLastPlayer: gameState.isLastPlayer || false,
      estimatedPiles: gameState.estimatedPiles || 0,
      handStrength: gameState.handStrength || 0,
      
      // Actions
      onDeclare: gameActions.makeDeclaration
    };
  }, [gameState, gameActions]);

  const turnProps = useMemo(() => {
    if (gameState.phase !== 'turn') return null;
    
    console.log(`🔢 GAMECONTAINER_DEBUG: gameState.currentTurnNumber = ${gameState.currentTurnNumber}`);
    console.log(`🔢 GAMECONTAINER_DEBUG: currentTurnPlays =`, gameState.currentTurnPlays);
    
    // Extract play type from the starter's play
    let playType = '';
    if (gameState.currentTurnPlays && gameState.currentTurnPlays.length > 0 && gameState.currentTurnStarter) {
      console.log('🎲 PLAYTYPE_DEBUG: currentTurnStarter:', gameState.currentTurnStarter);
      console.log('🎲 PLAYTYPE_DEBUG: currentTurnPlays:', gameState.currentTurnPlays);
      
      // Find the starter's play
      const starterPlay = gameState.currentTurnPlays.find(play => 
        play.player === gameState.currentTurnStarter
      );
      console.log('🎲 PLAYTYPE_DEBUG: starterPlay:', starterPlay);
      
      if (starterPlay) {
        // Check both camelCase and snake_case versions
        const extractedPlayType = starterPlay.playType || starterPlay.play_type;
        if (extractedPlayType && extractedPlayType !== 'UNKNOWN' && extractedPlayType !== 'unknown') {
          playType = extractedPlayType;
          console.log('🎲 PLAYTYPE_DEBUG: Found play type:', playType);
        }
      } else {
        console.log('🎲 PLAYTYPE_DEBUG: No starter play found');
      }
    }
    
    // Build piles won count from previous turns (would need to be tracked)
    const piecesWonCount = gameState.playerPiles || {};
    
    // Build player hand sizes - this would come from backend players data
    const playerHandSizes = {};
    if (gameState.players) {
      gameState.players.forEach(player => {
        // For current player, use actual hand length
        if (player.name === gameState.playerName) {
          playerHandSizes[player.name] = gameState.myHand.length;
        } else {
          // For others, backend should provide hand_size
          // Fallback to 8 minus played pieces count
          const playedCount = gameState.currentTurnPlays
            ? gameState.currentTurnPlays.filter(p => p.player === player.name).length * (gameState.requiredPieceCount || 1)
            : 0;
          playerHandSizes[player.name] = Math.max(0, 8 - playedCount);
        }
      });
    }
    
    return {
      // Data from backend
      myHand: gameState.myHand || [],
      players: gameState.players || [],
      currentPlayer: gameState.currentPlayer || '',
      playerName: gameState.playerName || '',
      currentTurnPlays: gameState.currentTurnPlays || [],
      requiredPieceCount: gameState.requiredPieceCount,
      turnNumber: gameState.currentTurnNumber || 1,
      piecesWonCount: piecesWonCount,
      previousWinner: gameState.currentTurnStarter || '',
      playType: playType,
      declarationData: gameState.declarations || {},
      playerHandSizes: playerHandSizes,
      
      // State calculated by backend
      isMyTurn: gameState.isMyTurn || false,
      canPlayAnyCount: gameState.canPlayAnyCount || false,
      
      // Actions
      onPlayPieces: gameActions.playPieces,
      onPass: gameActions.pass
    };
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
    
    // Determine if this is the last turn of the round
    const isLastTurn = gameState.players.every(player => {
      // Check if all players have empty hands (would need backend data)
      return false; // Default to false, backend should provide this
    });
    
    const props = {
      // Data from backend
      winner: gameState.turnWinner || null,
      winningPlay: gameState.winningPlay || null,
      playerPiles: gameState.playerPiles || {},
      players: gameState.players || [],
      turnNumber: gameState.currentTurnNumber || gameState.turnNumber || 1,
      roundNumber: gameState.currentRound || 1,
      nextStarter: gameState.nextStarter || null,
      playerName: gameState.playerName || '',
      isLastTurn: isLastTurn,
      currentTurnPlays: gameState.currentTurnPlays || [],
      
      // Actions
      onContinue: () => {
        // Backend handles auto-transition, this is just for manual continue if needed
        console.log('Turn results continue requested');
      }
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
            return (
              <GameLayout 
                phase="preparation" 
                roundNumber={gameState.currentRound}
                showMultiplier={gameState.redealMultiplier > 1}
                multiplierValue={gameState.redealMultiplier}
              >
                <PreparationUI {...preparationProps} />
              </GameLayout>
            );
            
          case 'declaration':
            return (
              <GameLayout 
                phase="declaration" 
                roundNumber={gameState.currentRound}
                showMultiplier={gameState.redealMultiplier > 1}
                multiplierValue={gameState.redealMultiplier}
              >
                <DeclarationUI {...declarationProps} />
              </GameLayout>
            );
            
          case 'turn':
            const turnRequirement = (() => {
              if (!turnProps) return null;
              const { currentPlayer, playerName, requiredPieceCount } = turnProps;
              const isMyTurn = currentPlayer === playerName;
              
              if (!isMyTurn) {
                return { type: 'waiting', text: `Waiting for ${currentPlayer} to play` };
              }
              
              if (requiredPieceCount === 0 || requiredPieceCount === null) {
                return { type: 'active', text: 'Play any number of pieces or pass' };
              }
              
              return { type: 'active', text: `Must play exactly ${requiredPieceCount} piece${requiredPieceCount > 1 ? 's' : ''}` };
            })();
            
            return (
              <GameLayout 
                phase="turn" 
                roundNumber={gameState.currentRound}
                showMultiplier={gameState.redealMultiplier > 1}
                multiplierValue={gameState.redealMultiplier}
                playType={turnProps?.playType || ''}
                currentPlayer={turnProps?.currentPlayer || ''}
                turnRequirement={turnRequirement}
              >
                <TurnUI {...turnProps} />
              </GameLayout>
            );
            
          case 'turn_results':
            console.log('🏆 GAMECONTAINER_DEBUG: Rendering TurnResultsUI with props:', turnResultsProps);
            return (
              <GameLayout 
                phase="turn_results" 
                roundNumber={gameState.currentRound}
                showMultiplier={gameState.redealMultiplier > 1}
                multiplierValue={gameState.redealMultiplier}
              >
                <TurnResultsUI {...turnResultsProps} />
              </GameLayout>
            );
            
          case 'scoring':
            return (
              <GameLayout 
                phase="scoring" 
                roundNumber={gameState.currentRound}
                showMultiplier={gameState.redealMultiplier > 1}
                multiplierValue={gameState.redealMultiplier}
              >
                <ScoringUI {...scoringProps} />
              </GameLayout>
            );
            
          case 'game_over':
            return (
              <GameLayout 
                phase="game_over" 
                roundNumber={gameState.currentRound}
                showMultiplier={false}
              >
                <GameOverUI {...gameOverProps} />
              </GameLayout>
            );
            
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