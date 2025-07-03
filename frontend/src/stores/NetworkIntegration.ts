// frontend/src/stores/NetworkIntegration.ts

import { networkService } from '../services/NetworkService';
import { gameStore } from './UnifiedGameStore';
import type { NetworkEventDetail } from '../services/types';

/**
 * NetworkIntegration - Bridges UnifiedGameStore with NetworkService
 * 
 * Listens to WebSocket events and updates the store accordingly.
 * This replaces the complex event handling in GameService.
 */
export class NetworkIntegration {
  private eventUnsubscribers: (() => void)[] = [];
  
  initialize(): void {
    this.setupEventListeners();
  }
  
  cleanup(): void {
    this.eventUnsubscribers.forEach(unsub => unsub());
    this.eventUnsubscribers = [];
  }
  
  private setupEventListeners(): void {
    // Connection events
    this.listenTo('connected', this.handleConnected);
    this.listenTo('disconnected', this.handleDisconnected);
    this.listenTo('reconnected', this.handleReconnected);
    
    // Room events
    this.listenTo('room_update', this.handleRoomUpdate);
    this.listenTo('player_joined', this.handlePlayerJoined);
    this.listenTo('player_left', this.handlePlayerLeft);
    this.listenTo('game_started', this.handleGameStarted);
    
    // Game events
    this.listenTo('phase_change', this.handlePhaseChange);
    this.listenTo('declare', this.handleDeclare);
    this.listenTo('play', this.handlePlay);
    this.listenTo('turn_complete', this.handleTurnComplete);
    this.listenTo('round_complete', this.handleRoundComplete);
    this.listenTo('game_over', this.handleGameOver);
    
    // Error events
    this.listenTo('error', this.handleError);
    this.listenTo('room_closed', this.handleRoomClosed);
  }
  
  private listenTo(event: string, handler: (detail: NetworkEventDetail) => void): void {
    const boundHandler = (e: Event) => {
      const detail = (e as CustomEvent<NetworkEventDetail>).detail;
      handler.call(this, detail);
    };
    
    networkService.addEventListener(event, boundHandler);
    this.eventUnsubscribers.push(() => {
      networkService.removeEventListener(event, boundHandler);
    });
  }
  
  // ===== Event Handlers =====
  
  private handleConnected = (detail: NetworkEventDetail): void => {
    gameStore.setState({
      connectionStatus: {
        isConnected: true,
        isConnecting: false,
        isReconnecting: false,
        error: null
      },
      roomId: detail.roomId
    });
  };
  
  private handleDisconnected = (detail: NetworkEventDetail): void => {
    gameStore.setState({
      connectionStatus: {
        isConnected: false,
        isConnecting: false,
        isReconnecting: false,
        error: detail.error || null
      }
    });
  };
  
  private handleReconnected = (detail: NetworkEventDetail): void => {
    gameStore.setState({
      connectionStatus: {
        isConnected: true,
        isConnecting: false,
        isReconnecting: false,
        error: null
      }
    });
  };
  
  private handleRoomUpdate = (detail: NetworkEventDetail): void => {
    const { players, host_name, started } = detail.data;
    
    gameStore.setState(state => ({
      gameState: {
        ...state.gameState,
        players: players || state.gameState.players,
        isHost: state.playerName === host_name
      },
      gameStarted: started || false
    }));
  };
  
  private handlePlayerJoined = (detail: NetworkEventDetail): void => {
    const { player_name, slot_id } = detail.data;
    
    gameStore.setState(state => {
      const players = [...state.gameState.players];
      if (slot_id && slot_id <= 4) {
        players[slot_id - 1] = { name: player_name, is_bot: false };
      }
      return { 
        gameState: {
          ...state.gameState,
          players
        }
      };
    });
  };
  
  private handlePlayerLeft = (detail: NetworkEventDetail): void => {
    const { player_name } = detail.data;
    
    gameStore.setState(state => ({
      gameState: {
        ...state.gameState,
        players: state.gameState.players.filter(p => p.name !== player_name)
      }
    }));
  };
  
  private handleGameStarted = (detail: NetworkEventDetail): void => {
    gameStore.setState({
      gameStarted: true
    });
  };
  
  private handlePhaseChange = (detail: NetworkEventDetail): void => {
    const { 
      phase, 
      phase_data, 
      allowed_actions, 
      players,
      version,
      checksum,
      server_timestamp
    } = detail.data;
    
    console.log('🔄 PHASE_CHANGE_DEBUG: Received phase_change event:', {
      phase,
      phase_data: Object.keys(phase_data || {}),
      reason: detail.data.reason,
      reconnect_sync: detail.data.reconnect_sync,
      round: detail.data.round
    });
    
    // Handle versioned update from backend
    if (version && checksum) {
      gameStore.handleBackendUpdate(version, checksum, {
        phase,
        ...phase_data
      });
    } else {
      // Fallback for non-versioned updates (during transition)
      gameStore.updateGameState({
        phase,
        ...phase_data
      });
    }
    
    // Update top-level state
    gameStore.setState({
      gamePhase: phase,
      phaseData: phase_data || {}
    });
    
    // Update derived state
    const playerName = gameStore.getState().playerName;
    if (playerName && phase_data) {
      const isMyTurn = phase_data.current_player === playerName;
      const canPlayAnyCount = phase_data.current_turn_starter === playerName && 
                             !phase_data.required_piece_count;
      
      gameStore.updateGameState({
        isMyTurn,
        canPlayAnyCount,
        currentRound: detail.data.round || gameStore.getState().gameState.currentRound,
        turnNumber: phase_data.current_turn_number || gameStore.getState().gameState.turnNumber,
        currentTurnNumber: phase_data.current_turn_number || gameStore.getState().gameState.currentTurnNumber
      });
      
      gameStore.setState({
        roundNumber: detail.data.round || gameStore.getState().roundNumber
      });
    }
  };
  
  private handleDeclare = (detail: NetworkEventDetail): void => {
    const { player, declaration, all_declared } = detail.data;
    
    gameStore.setState(state => {
      const phaseData = { ...state.phaseData };
      if (!phaseData.declarations) {
        phaseData.declarations = {};
      }
      phaseData.declarations[player] = declaration;
      
      return { phaseData };
    });
    
    gameStore.updateGameState({
      declarations: {
        ...gameStore.getState().gameState.declarations,
        [player]: declaration
      }
    });
  };
  
  private handlePlay = (detail: NetworkEventDetail): void => {
    const { player, pieces, next_player, required_count } = detail.data;
    
    gameStore.setState(state => {
      const phaseData = { ...state.phaseData };
      phaseData.current_player = next_player;
      phaseData.required_piece_count = required_count;
      
      return { phaseData };
    });
    
    gameStore.updateGameState({
      isMyTurn: next_player === gameStore.getState().playerName,
      requiredPieceCount: required_count
    });
  };
  
  private handleTurnComplete = (detail: NetworkEventDetail): void => {
    const { winner, piles_won, next_starter } = detail.data;
    
    gameStore.setState(state => {
      const phaseData = { ...state.phaseData };
      phaseData.last_turn_winner = winner;
      phaseData.current_turn_starter = next_starter;
      
      return { phaseData };
    });
    
    gameStore.updateGameState({
      turnWinner: winner,
      nextStarter: next_starter
    });
  };
  
  private handleRoundComplete = (detail: NetworkEventDetail): void => {
    const { round_scores, total_scores } = detail.data;
    
    gameStore.setState({
      scores: total_scores || {}
    });
    
    gameStore.updateGameState({
      roundScores: round_scores || {},
      totalScores: total_scores || {}
    });
  };
  
  private handleGameOver = (detail: NetworkEventDetail): void => {
    const { winners, final_scores } = detail.data;
    
    gameStore.updateGameState({
      gameOver: true,
      winners: winners || [],
      totalScores: final_scores || {}
    });
    
    gameStore.setState({
      gamePhase: 'scoring',
      scores: final_scores || {}
    });
  };
  
  private handleError = (detail: NetworkEventDetail): void => {
    gameStore.setState({
      error: detail.data.message || 'Unknown error'
    });
  };
  
  private handleRoomClosed = (detail: NetworkEventDetail): void => {
    gameStore.setState({
      roomId: null,
      gameStarted: false,
      gamePhase: null,
      gameState: gameStore['getInitialGameState'](),
      error: 'Room closed'
    });
  };
}

// Create and export singleton instance
export const networkIntegration = new NetworkIntegration();