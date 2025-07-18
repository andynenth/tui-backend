/**
 * 🎮 **GameService** - Single Source of Truth for Game State (TypeScript)
 * 
 * Phase 1, Task 1.2: Foundation Services
 * 
 * Features:
 * ✅ Single source of truth for all game state
 * ✅ Centralized event handling from backend
 * ✅ Observable pattern for React integration
 * ✅ Immutable state updates
 * ✅ Action dispatching to backend
 * ✅ Complete 4-phase game flow support
 * ✅ Derived state calculations (isMyTurn, etc.)
 * ✅ State validation and error handling
 * ✅ Full TypeScript type safety
 */

import { networkService } from './NetworkService';
import type {
  GameState,
  PhaseData,
  StateChangeEvent,
  GameEventType,
  GameAction,
  StateListener,
  CleanupFunction,
  NetworkEventDetail
} from './types';

export class GameService extends EventTarget {
  // Singleton instance
  private static instance: GameService | null = null;
  
  /**
   * Get the singleton instance
   */
  static getInstance(): GameService {
    if (!GameService.instance) {
      GameService.instance = new GameService();
    }
    return GameService.instance;
  }

  private state: GameState;
  private readonly listeners = new Set<StateListener>();
  private isDestroyed = false;
  private readonly eventHistory: StateChangeEvent[] = [];
  private sequenceNumber = 0;

  private constructor() {
    super();
    
    if (GameService.instance) {
      throw new Error('GameService is a singleton. Use GameService.getInstance()');
    }

    // Initialize state
    this.state = this.getInitialState();

    // Set up network event listeners
    this.setupNetworkListeners();
  }

  // ===== PUBLIC API =====

  /**
   * Get current game state (immutable)
   */
  getState(): Readonly<GameState> {
    return Object.freeze({ ...this.state });
  }

  /**
   * Connect to a game room
   */
  async joinRoom(roomId: string, playerName: string): Promise<void> {
    if (this.isDestroyed) {
      throw new Error('GameService has been destroyed');
    }

    try {
      // Connect to room via NetworkService
      await networkService.connectToRoom(roomId);
      
      // Update local state
      this.setState({
        ...this.state,
        roomId,
        playerName,
        isConnected: true,
        error: null
      }, 'JOIN_ROOM');

      console.log(`🎮 GameService: Joined room ${roomId} as ${playerName}`);
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      this.setState({
        ...this.state,
        error: `Failed to join room: ${errorMessage}`,
        isConnected: false
      }, 'JOIN_ROOM_FAILED');
      
      throw error;
    }
  }

  /**
   * Leave current room
   */
  async leaveRoom(): Promise<void> {
    if (this.state.roomId) {
      await networkService.disconnectFromRoom(this.state.roomId);
      
      this.setState({
        ...this.getInitialState(),
        playerName: this.state.playerName // Preserve player name
      }, 'LEAVE_ROOM');
      
      console.log('🎮 GameService: Left room');
    }
  }

  // ===== GAME ACTIONS =====

  /**
   * Accept redeal during preparation phase
   */
  acceptRedeal(): void {
    this.validateAction('ACCEPT_REDEAL', 'preparation');
    this.sendAction('accept_redeal', {});
  }

  /**
   * Decline redeal during preparation phase
   */
  declineRedeal(): void {
    this.validateAction('DECLINE_REDEAL', 'preparation');
    this.sendAction('decline_redeal', {});
  }

  /**
   * Make declaration during declaration phase
   */
  makeDeclaration(value: number): void {
    this.validateAction('MAKE_DECLARATION', 'declaration');
    
    if (typeof value !== 'number' || value < 0 || value > 8) {
      throw new Error(`Invalid declaration value: ${value}. Must be 0-8.`);
    }

    // Check if it's player's turn
    if (this.state.currentDeclarer !== this.state.playerName) {
      throw new Error('Not your turn to declare');
    }

    // Check last player total=8 restriction
    const declarationCount = Object.keys(this.state.declarations).length;
    const totalPlayers = this.state.players.length;
    if (declarationCount === totalPlayers - 1) {
      const currentTotal = (Object.values(this.state.declarations) as number[]).reduce((sum: number, val: number) => sum + val, 0);
      if (currentTotal + value === 8) {
        throw new Error('Last player cannot make total equal 8');
      }
    }

    this.sendAction('declare', { value, player_name: this.state.playerName });
  }

  /**
   * Play pieces during turn phase
   */
  playPieces(indices: number[]): void {
    this.validateAction('PLAY_PIECES', 'turn');
    
    if (!Array.isArray(indices) || indices.length === 0) {
      throw new Error('Must select at least one piece to play');
    }

    if (indices.some(i => i < 0 || i >= this.state.myHand.length)) {
      throw new Error('Invalid piece indices');
    }

    // Check if it's player's turn
    if (!this.state.isMyTurn) {
      throw new Error('Not your turn to play');
    }

    // Validate piece count matches required (if set)
    if (this.state.requiredPieceCount !== null && indices.length !== this.state.requiredPieceCount) {
      throw new Error(`Must play exactly ${this.state.requiredPieceCount} pieces`);
    }

    // Calculate total value of selected pieces
    const selectedPieces = indices.map(i => this.state.myHand[i]);
    const totalValue = selectedPieces.reduce((sum, piece) => sum + (piece.point || piece.value || 0), 0);

    this.sendAction('play', { 
      piece_indices: indices, 
      player_name: this.state.playerName,
      play_value: totalValue
    });
  }

  /**
   * Start next round (from scoring phase)
   */
  startNextRound(): void {
    this.validateAction('START_NEXT_ROUND', 'scoring');
    this.sendAction('start_next_round', {});
  }


  // ===== STATE MANAGEMENT =====

  /**
   * Add state change listener
   */
  addListener(callback: StateListener): CleanupFunction {
    if (typeof callback !== 'function') {
      throw new Error('Listener must be a function');
    }
    
    this.listeners.add(callback);
    
    return () => {
      this.listeners.delete(callback);
    };
  }

  /**
   * Remove state change listener
   */
  removeListener(callback: StateListener): void {
    this.listeners.delete(callback);
  }

  /**
   * Remove all listeners
   */
  removeAllListeners(): void {
    this.listeners.clear();
  }

  /**
   * Get event history (for debugging)
   */
  getEventHistory(): StateChangeEvent[] {
    return [...this.eventHistory];
  }

  /**
   * Replay to specific sequence number (for debugging)
   */
  replayToSequence(targetSequence: number): void {
    const initialState = this.getInitialState();
    const eventsToReplay = this.eventHistory.filter(e => e.sequence <= targetSequence);
    
    this.state = eventsToReplay.reduce((state, event) => 
      this.applyEvent(state, event), initialState);
    
    this.notifyListeners();
    console.log(`🔄 Replayed to sequence ${targetSequence}`);
  }

  /**
   * Destroy the service
   */
  destroy(): void {
    this.isDestroyed = true;
    this.listeners.clear();
    this.eventHistory.length = 0;
    
    // Reset singleton
    GameService.instance = null;
    
    console.log('🎮 GameService: Destroyed');
  }

  // ===== PRIVATE METHODS =====

  /**
   * Get initial state
   */
  private getInitialState(): GameState {
    return {
      // Connection state
      isConnected: false,
      roomId: null,
      playerName: null,
      
      // Game state
      phase: 'waiting',
      currentRound: 0,
      players: [],
      roundStarter: null,
      
      // Preparation phase state
      weakHands: [],
      currentWeakPlayer: null,
      redealRequests: {},
      redealMultiplier: 1,
      
      // Declaration phase state
      myHand: [],
      declarations: {},
      declarationOrder: [],
      currentDeclarer: null,
      declarationTotal: 0,
      
      // Turn phase state
      currentTurnStarter: null,
      turnOrder: [],
      currentPlayer: null,
      currentTurnPlays: [],
      requiredPieceCount: null,
      currentTurnNumber: 0,
      
      // Scoring phase state
      roundScores: {},
      totalScores: {},
      winners: [],
      
      // Turn results phase state
      turnWinner: null,
      winningPlay: null,
      playerPiles: {},
      turnNumber: 1,
      nextStarter: null,
      allHandsEmpty: false,
      willContinue: false,
      
      // UI state
      isMyTurn: false,
      allowedActions: [],
      validOptions: [],
      
      // Meta state
      lastEventSequence: 0,
      error: null,
      gameOver: false
    };
  }

  /**
   * Set up network event listeners
   */
  private setupNetworkListeners(): void {
    // Connection events
    networkService.addEventListener('connected', this.handleNetworkConnection.bind(this));
    networkService.addEventListener('disconnected', this.handleNetworkDisconnection.bind(this));
    
    // Game events
    const gameEvents: GameEventType[] = [
      'phase_change',
      'weak_hands_found',
      'redeal_decision_needed', 
      'redeal_executed',
      'declare',
      'play',
      'turn_complete',
      'turn_resolved',
      'score_update',
      'round_complete',
      'game_ended'
    ];
    
    gameEvents.forEach(event => {
      networkService.addEventListener(event, this.handleNetworkEvent.bind(this));
    });
  }

  /**
   * Handle network connection
   */
  private handleNetworkConnection(): void {
    // Connection established - update state
    
    this.setState({
      ...this.state,
      isConnected: true,
      error: null
    }, 'NETWORK_CONNECTED');
  }

  /**
   * Handle network disconnection
   */
  private handleNetworkDisconnection(event: Event): void {
    const customEvent = event as CustomEvent<{ intentional: boolean }>;
    const { intentional } = customEvent.detail;
    
    this.setState({
      ...this.state,
      isConnected: false,
      error: intentional ? null : 'Connection lost'
    }, 'NETWORK_DISCONNECTED');
  }

  /**
   * Handle network events
   */
  private handleNetworkEvent(event: Event): void {
    const customEvent = event as CustomEvent<NetworkEventDetail>;
    const { roomId, data } = customEvent.detail;
    
    console.log(`🌐 FRONTEND_EVENT_DEBUG: Received ${event.type} event for room ${roomId}`, data);
    
    // Only process events for our room
    if (roomId !== this.state.roomId) {
      console.log(`🌐 FRONTEND_EVENT_DEBUG: Ignoring event for different room (ours: ${this.state.roomId})`);
      return;
    }
    
    try {
      const newState = this.processGameEvent(event.type, data);
      this.setState(newState, `NETWORK_EVENT:${event.type.toUpperCase()}`);
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error(`Failed to process ${event.type} event:`, error);
      this.setState({
        ...this.state,
        error: `Event processing error: ${errorMessage}`
      }, 'EVENT_ERROR');
    }
  }

  /**
   * Process game events from backend
   */
  private processGameEvent(eventType: string, data: any): GameState {
    let newState = { ...this.state };
    
    switch (eventType) {
      case 'phase_change':
        newState = this.handlePhaseChange(newState, data);
        break;
        
      case 'weak_hands_found':
        newState = this.handleWeakHandsFound(newState, data);
        break;
        
      case 'redeal_decision_needed':
        newState = this.handleRedealDecisionNeeded(newState, data);
        break;
        
      case 'redeal_executed':
        newState = this.handleRedealExecuted(newState, data);
        break;
        
      case 'declare':
        newState = this.handleDeclare(newState, data);
        break;
        
      case 'play':
        console.log(`🌐 PROCESS_EVENT_DEBUG: Handling play event`);
        newState = this.handlePlay(newState, data);
        break;
        
      case 'turn_resolved':
        console.log(`🌐 PROCESS_EVENT_DEBUG: Handling turn_resolved event`);
        newState = this.handleTurnResolved(newState, data);
        break;
        
      case 'turn_complete':
        console.log(`🌐 PROCESS_EVENT_DEBUG: Handling turn_complete event with data:`, data);
        console.log(`🏆 TURN_COMPLETE_RAW_DEBUG: Event data received:`, JSON.stringify(data, null, 2));
        newState = this.handleTurnComplete(newState, data);
        break;
        
      case 'score_update':
        newState = this.handleScoreUpdate(newState, data);
        break;
        
      case 'round_complete':
        newState = this.handleRoundComplete(newState, data);
        break;
        
      case 'game_ended':
        newState = this.handleGameEnded(newState, data);
        break;
        
      default:
        console.warn(`🌐 PROCESS_EVENT_DEBUG: Unknown game event: ${eventType}`, data);
        return newState;
    }
    
    console.log(`🌐 PROCESS_EVENT_DEBUG: Event ${eventType} processed, updating derived state`);
    // Update derived state
    newState = this.updateDerivedState(newState);
    
    console.log(`🌐 PROCESS_EVENT_DEBUG: Finished processing ${eventType} event`);
    return newState;
  }

  /**
   * Handle phase change events
   */
  private handlePhaseChange(state: GameState, data: any): GameState {
    const newState = { ...state };
    
    newState.phase = data.phase;
    newState.currentRound = data.round || state.currentRound;
    
    console.log(`🔄 PHASE_CHANGE_DEBUG: Phase: ${data.phase}`);
    console.log(`🔄 PHASE_CHANGE_DEBUG: Data players:`, data.players);
    console.log(`🔄 PHASE_CHANGE_DEBUG: Data phase_data:`, data.phase_data);
    console.log(`🔄 PHASE_CHANGE_DEBUG: First player raw:`, Object.keys(data.players)[0], data.players[Object.keys(data.players)[0]]);
    
    // Extract my hand from players data (sent by backend)
    if (data.players && state.playerName && data.players[state.playerName]) {
      const myPlayerData = data.players[state.playerName];
      if (myPlayerData.hand) {
        // Convert string pieces back to objects for frontend
        newState.myHand = myPlayerData.hand.map((pieceStr: string) => {
          // Parse piece strings like "ELEPHANT_RED(10)" into objects
          const match = pieceStr.match(/^(.+)\((\d+)\)$/);
          if (match) {
            const [, name, value] = match;
            const [piece, color] = name.split('_');
            return {
              color, // Use 'color' property that GamePiece expects
              point: parseInt(value),
              kind: piece,
              name: piece.toLowerCase(),
              displayName: `${piece} ${color}`
            };
          }
          return { color: 'UNKNOWN', point: 0, kind: 'UNKNOWN', name: pieceStr, displayName: pieceStr };
        });
      }
    }
    
    // Convert players dictionary to array for UI components
    if (data.players) {
      newState.players = Object.entries(data.players).map(([playerName, playerData]: [string, any]) => ({
        name: playerName, // Use the key as the name
        is_bot: playerData.is_bot || false,
        is_host: playerData.is_host || false,
        zero_declares_in_a_row: playerData.zero_declares_in_a_row || 0
      }));
      console.log(`🔄 PHASE_CHANGE_DEBUG: Converted players array:`, newState.players);
      console.log(`🔄 PHASE_CHANGE_DEBUG: Sample player object:`, newState.players[0]);
    }
    
    // Extract phase-specific data
    if (data.phase_data) {
      const phaseData: PhaseData = data.phase_data;
      
      // Update players list (prefer backend phase_data over data.players for player metadata)
      if (phaseData.players) {
        newState.players = phaseData.players;
      }
      
      // Phase-specific updates
      switch (data.phase) {
        case 'preparation':
          // Fallback to phase_data.my_hand if data.players doesn't have it
          if (phaseData.my_hand && !newState.myHand.length) {
            newState.myHand = phaseData.my_hand;
          }
          if (phaseData.round_starter) newState.roundStarter = phaseData.round_starter;
          newState.redealMultiplier = phaseData.redeal_multiplier || 1;
          if (phaseData.weak_hands) newState.weakHands = phaseData.weak_hands;
          if (phaseData.current_weak_player) newState.currentWeakPlayer = phaseData.current_weak_player;
          
          // Calculate preparation-specific UI state
          if (newState.myHand.length > 0) {
            newState.isMyHandWeak = this.calculateWeakHand(newState.myHand);
            newState.handValue = this.calculateHandValue(newState.myHand);
            newState.highestCardValue = this.calculateHighestCardValue(newState.myHand);
          }
          if (phaseData.current_weak_player && newState.playerName) {
            newState.isMyDecision = phaseData.current_weak_player === newState.playerName;
          }
          break;
          
        case 'declaration':
          // Fallback to phase_data.my_hand if data.players doesn't have it
          if (phaseData.my_hand && !newState.myHand.length) {
            newState.myHand = phaseData.my_hand;
          }
          if (phaseData.declaration_order) newState.declarationOrder = phaseData.declaration_order;
          if (phaseData.current_declarer) newState.currentDeclarer = phaseData.current_declarer;
          newState.declarations = phaseData.declarations || {};
          
          // Calculate declaration-specific UI state
          // Use backend's calculated values first, fallback to frontend calculation
          newState.currentTotal = phaseData.declaration_total ?? 
            Object.values(phaseData.declarations || {}).reduce((sum: number, val: number) => sum + val, 0);
          
          if (phaseData.declaration_order) {
            newState.declarationProgress = {
              declared: Object.keys(phaseData.declarations || {}).length,
              total: phaseData.declaration_order.length
            };
            newState.isLastPlayer = Object.keys(phaseData.declarations || {}).length === phaseData.declaration_order.length - 1;
          } else if (phaseData.players) {
            newState.declarationProgress = {
              declared: Object.keys(phaseData.declarations || {}).length,
              total: phaseData.players.length
            };
            newState.isLastPlayer = Object.keys(phaseData.declarations || {}).length === phaseData.players.length - 1;
          }
          if (newState.myHand.length > 0) {
            newState.estimatedPiles = this.calculateEstimatedPiles(newState.myHand);
            newState.handStrength = this.calculateHandStrength(newState.myHand);
          }
          break;
          
        case 'turn':
          if (phaseData.turn_order) newState.turnOrder = phaseData.turn_order;
          if (phaseData.current_turn_starter) newState.currentTurnStarter = phaseData.current_turn_starter;
          if (phaseData.current_player) newState.currentPlayer = phaseData.current_player;
          
          // 🚀 ENTERPRISE FIX: Use backend's required_piece_count as single source of truth
          if (phaseData.required_piece_count !== undefined) {
            newState.requiredPieceCount = phaseData.required_piece_count;
            console.log(`🎯 REQUIRED_COUNT_FIX: Set requiredPieceCount to ${phaseData.required_piece_count} from backend phase_data`);
          }
          
          // 🎯 ROUND/TURN TRACKING DEBUG: Log comprehensive turn state
          const roundNum = newState.currentRound || 0;
          const turnNum = phaseData.current_turn_number || 0;
          const starter = phaseData.current_turn_starter || 'unknown';
          const currentPlayer = phaseData.current_player || 'unknown';
          const requiredCount = phaseData.required_piece_count;
          const playsCount = phaseData.turn_plays ? Object.keys(phaseData.turn_plays).length : 0;
          
          console.log(`🔢 FRONTEND_ROUND_TURN_DEBUG: Round ${roundNum}, Turn ${turnNum}`);
          console.log(`🎯 FRONTEND_TURN_STATE: Starter: ${starter}, Current: ${currentPlayer}, Required: ${requiredCount}, Plays: ${playsCount}`);
          
          // Convert backend's turn_plays dictionary to frontend's currentTurnPlays array
          if (phaseData.turn_plays && typeof phaseData.turn_plays === 'object') {
            newState.currentTurnPlays = Object.entries(phaseData.turn_plays).map(([playerName, playData]: [string, any]) => {
              const playType = playData.play_type || 'UNKNOWN';
              // A play is invalid if explicitly marked as invalid OR if play_type is 'INVALID'
              const isValid = playData.is_valid !== false && playType !== 'INVALID';
              
              return {
                player: playerName,
                cards: playData.pieces || [],
                isValid,
                playType,
                totalValue: playData.play_value || 0
              };
            });
            console.log(`🎲 TURN_PLAYS_DEBUG: Converted ${Object.keys(phaseData.turn_plays).length} plays to currentTurnPlays:`, newState.currentTurnPlays);
          } else {
            newState.currentTurnPlays = phaseData.current_turn_plays || [];
          }
          
          console.log(`🔢 FRONTEND_TURN_DEBUG: phaseData.current_turn_number = ${phaseData.current_turn_number}`);
          newState.currentTurnNumber = phaseData.current_turn_number || 0;
          
          // Calculate turn-specific UI state
          newState.canPlayAnyCount = !newState.requiredPieceCount && newState.isMyTurn;
          newState.selectedPlayValue = 0; // Will be updated when player selects pieces
          break;
          
        case 'scoring':
          console.log('🏆 SCORING_FRONTEND_DEBUG: Processing scoring phase data');
          console.log('📊 Raw phase data:', phaseData);
          console.log('👥 Available players in newState:', newState.players);
          
          // Process backend scoring objects to extract numeric values
          const processedRoundScores: Record<string, number> = {};
          const rawRoundScores = phaseData.round_scores || {};
          
          console.log('📊 SCORING_DEBUG: Raw round scores:', rawRoundScores);
          
          Object.entries(rawRoundScores).forEach(([playerName, scoreData]) => {
            // Handle backend scoring objects vs simple numbers
            if (typeof scoreData === 'object' && scoreData !== null) {
              if (scoreData.final_score !== undefined) {
                processedRoundScores[playerName] = scoreData.final_score;
              } else {
                // Object without final_score - default to 0
                processedRoundScores[playerName] = 0;
              }
            } else {
              // Simple number or null
              processedRoundScores[playerName] = scoreData || 0;
            }
          });
          
          newState.roundScores = processedRoundScores;
          
          // Also process total_scores in case they're objects
          const processedTotalScores: Record<string, number> = {};
          const rawTotalScores = phaseData.total_scores || {};
          
          Object.entries(rawTotalScores).forEach(([playerName, scoreData]) => {
            // Handle backend scoring objects vs simple numbers
            if (typeof scoreData === 'object' && scoreData !== null) {
              if (scoreData.total_score !== undefined) {
                processedTotalScores[playerName] = scoreData.total_score;
              } else {
                // Object without total_score - default to 0
                processedTotalScores[playerName] = 0;
              }
            } else {
              // Simple number or null
              processedTotalScores[playerName] = scoreData || 0;
            }
          });
          
          newState.totalScores = processedTotalScores;
          
          // Set scoring-specific state
          newState.gameOver = phaseData.game_complete || false;
          newState.winners = phaseData.winners || [];
          newState.redealMultiplier = phaseData.redeal_multiplier || 1;
          
          console.log('✅ SCORING_DEBUG: Processed round scores:', processedRoundScores);
          console.log('✅ SCORING_DEBUG: Processed total scores:', processedTotalScores);
          console.log('✅ SCORING_DEBUG: Game over:', newState.gameOver);
          console.log('✅ SCORING_DEBUG: Winners:', newState.winners);
          console.log('✅ SCORING_DEBUG: Redeal multiplier:', newState.redealMultiplier);
          
          // Calculate scoring-specific UI state
          if (phaseData.players && phaseData.round_scores && phaseData.total_scores) {
            console.log('🧮 SCORING_DEBUG: Calculating playersWithScores...');
            newState.playersWithScores = this.calculatePlayersWithScores(
              phaseData.players, 
              phaseData.round_scores, 
              phaseData.total_scores,
              phaseData.redeal_multiplier || 1,
              phaseData.winners || []
            );
            console.log('🧮 SCORING_DEBUG: Generated playersWithScores:', newState.playersWithScores);
          } else {
            console.log('⚠️ SCORING_DEBUG: Missing data for playersWithScores calculation');
            console.log('   players available:', !!phaseData.players, phaseData.players);
            console.log('   round_scores available:', !!phaseData.round_scores, Object.keys(phaseData.round_scores || {}));
            console.log('   total_scores available:', !!phaseData.total_scores, phaseData.total_scores);
            
            // Fallback: try to use newState.players if phaseData.players is missing
            if (!phaseData.players && newState.players && newState.players.length > 0) {
              console.log('🔧 SCORING_DEBUG: Using newState.players as fallback...');
              if (phaseData.round_scores && phaseData.total_scores) {
                newState.playersWithScores = this.calculatePlayersWithScores(
                  newState.players,
                  phaseData.round_scores,
                  phaseData.total_scores,
                  phaseData.redeal_multiplier || 1,
                  phaseData.winners || []
                );
                console.log('🧮 SCORING_DEBUG: Generated playersWithScores with fallback:', newState.playersWithScores);
              }
            }
          }
          break;
      }
    }
    
    // Clear error on successful phase change
    newState.error = null;
    
    return newState;
  }

  /**
   * Handle weak hands found event
   */
  private handleWeakHandsFound(state: GameState, data: any): GameState {
    return {
      ...state,
      weakHands: data.weak_hands || [],
      currentWeakPlayer: data.current_weak_player || null
    };
  }

  /**
   * Handle redeal decision needed event
   */
  private handleRedealDecisionNeeded(state: GameState, data: any): GameState {
    return {
      ...state,
      currentWeakPlayer: data.player
    };
  }

  /**
   * Handle redeal executed event
   */
  private handleRedealExecuted(state: GameState, data: any): GameState {
    return {
      ...state,
      myHand: data.my_hand || state.myHand,
      redealMultiplier: data.redeal_multiplier || state.redealMultiplier,
      weakHands: [],
      currentWeakPlayer: null,
      redealRequests: {}
    };
  }

  /**
   * Handle declare event
   */
  private handleDeclare(state: GameState, data: any): GameState {
    console.log(`🎯 DECLARE_DEBUG: RECEIVED declare event!`, data);
    const newDeclarations = {
      ...state.declarations,
      [data.player]: data.value
    };
    
    const declarationTotal = (Object.values(newDeclarations) as number[]).reduce((sum: number, val: number) => sum + val, 0);
    
    // Find next declarer
    const currentIndex = state.declarationOrder.indexOf(data.player);
    const nextIndex = currentIndex + 1;
    const nextDeclarer = nextIndex < state.declarationOrder.length ? 
      state.declarationOrder[nextIndex] : null;
    
    console.log(`🎯 DECLARE_DEBUG: Player ${data.player} declared ${data.value}`);
    console.log(`🎯 DECLARE_DEBUG: New declarations:`, newDeclarations);
    console.log(`🎯 DECLARE_DEBUG: Declaration total: ${declarationTotal}`);
    console.log(`🎯 DECLARE_DEBUG: Next declarer: ${nextDeclarer}`);
    
    // Calculate derived state for declaration phase
    const newState = {
      ...state,
      declarations: newDeclarations,
      declarationTotal,
      currentDeclarer: nextDeclarer,
      currentTotal: declarationTotal, // Add this for UI
    };
    
    // Update declaration progress - use declarationOrder length if players not available
    const totalPlayers = (state.players && state.players.length > 0) 
      ? state.players.length 
      : (state.declarationOrder && state.declarationOrder.length > 0)
        ? state.declarationOrder.length
        : 4; // fallback to 4 players
        
    newState.declarationProgress = {
      declared: Object.keys(newDeclarations).length,
      total: totalPlayers
    };
    
    console.log(`🎯 DECLARE_DEBUG: Updated state currentTotal: ${newState.currentTotal}`);
    console.log(`🎯 DECLARE_DEBUG: Updated declarationProgress:`, newState.declarationProgress);
    
    return newState;
  }

  /**
   * Handle play event
   */
  private handlePlay(state: GameState, data: any): GameState {
    // 🎯 ROUND/TURN TRACKING DEBUG: Log play event with round/turn context
    const roundNum = state.currentRound || 0;
    const turnNum = state.currentTurnNumber || 0;
    const requiredCount = data.required_count || state.requiredPieceCount;
    
    console.log(`🎲 PLAY_DEBUG: Round ${roundNum}, Turn ${turnNum} - ${data.player} played ${data.pieces?.length || 0} pieces`);
    console.log(`🎲 PLAY_DEBUG: Required count: ${requiredCount}, Turn complete: ${data.turn_complete}, Next: ${data.next_player}`);
    console.log(`🎲 PLAY_DEBUG: Pieces data:`, data.pieces);
    
    // 🚀 ENTERPRISE: With enterprise architecture, phase_change events contain complete turn_plays data
    // Individual play events are only used for immediate UI feedback, phase_change has authoritative data
    
    // Check if we need to transition from turn_results back to turn phase
    let newPhase = state.phase;
    
    if (state.phase === 'turn_results') {
      // We're getting a play event while in turn_results, this means a new turn has started
      console.log(`🎯 PHASE_TRANSITION_DEBUG: Transitioning from turn_results to turn (new turn started)`);
      newPhase = 'turn';
    }
    
    // Transform backend data structure to frontend format for immediate feedback
    const playData = {
      player: data.player,
      cards: data.pieces || [], // Backend sends 'pieces', frontend expects 'cards'
      isValid: data.is_valid,
      playType: data.play_type,
      totalValue: data.play_value || 0
    };
    
    console.log(`🎲 PLAY_DEBUG: Transformed play data:`, playData);
    console.log(`🎲 PLAY_DEBUG: Cards array:`, playData.cards);
    
    // Note: We don't update currentTurnPlays here anymore since enterprise phase_change events
    // contain the authoritative turn_plays data. This prevents conflicts and ensures consistency.
    
    // 🚀 ENTERPRISE FIX: Don't set requiredPieceCount from play events
    // The backend phase_change events contain the authoritative required_piece_count
    // Setting it here from play events can cause stale data conflicts
    console.log(`🎯 PLAY_EVENT_DEBUG: NOT setting requiredPieceCount from play event (backend phase_change is authoritative)`);
    
    // Reset required piece count when starting new turn  
    let requiredPieceCount = state.requiredPieceCount;
    if (newPhase === 'turn' && state.phase === 'turn_results') {
      requiredPieceCount = null;
      console.log(`🎯 PHASE_TRANSITION_DEBUG: Reset requiredPieceCount for new turn`);
    }
    
    // Update current player from the play event
    let newCurrentPlayer = state.currentPlayer;
    if (data.next_player) {
      newCurrentPlayer = data.next_player;
      console.log(`🎯 PLAY_DEBUG: Updated currentPlayer from ${state.currentPlayer} to ${data.next_player}`);
    } else if (data.turn_complete) {
      console.log(`🎯 PLAY_DEBUG: Turn is complete but no next_player - turn should be finishing`);
    }
    
    // Check if turn is complete
    if (data.turn_complete) {
      console.log(`🎯 TURN_COMPLETE_FRONTEND: Turn marked as complete by backend`);
    }
    
    return {
      ...state,
      phase: newPhase,
      // Don't override currentTurnPlays - let phase_change events be authoritative 
      // currentTurnPlays: managed by phase_change events in enterprise architecture
      requiredPieceCount,
      currentPlayer: newCurrentPlayer,
      // Clear turn results data when transitioning to new turn
      ...(newPhase === 'turn' && state.phase === 'turn_results' ? {
        turnWinner: null,
        winningPlay: null,
        currentTurnPlays: [] // Clear turn plays when transitioning to new turn
      } : {})
    };
  }

  /**
   * Handle turn resolved event
   */
  private handleTurnResolved(state: GameState, data: any): GameState {
    return {
      ...state,
      currentTurnPlays: [],
      requiredPieceCount: null,
      myHand: data.my_hand || state.myHand,
      currentTurnNumber: state.currentTurnNumber + 1
    };
  }

  /**
   * Handle turn complete event - show turn results
   */
  private handleTurnComplete(state: GameState, data: any): GameState {
    // 🎯 ROUND/TURN TRACKING DEBUG: Log turn complete with round/turn context
    const roundNum = state.currentRound || 0;
    const turnNum = data.turn_number || state.currentTurnNumber || 0;
    const winner = data.winner || 'No winner';
    
    console.log(`🏆 TURN_COMPLETE_DEBUG: Round ${roundNum}, Turn ${turnNum} completed!`);
    console.log(`🏆 TURN_WINNER_DEBUG: Winner: ${winner}, Next starter: ${data.next_starter || 'Unknown'}`);
    console.log(`🏆 TURN_COMPLETE_DATA:`, data);
    
    const newState = {
      ...state,
      phase: 'turn_results',
      turnWinner: data.winner || null,
      winningPlay: data.winning_play || null,
      playerPiles: data.player_piles || {},
      turnNumber: data.turn_number || state.currentTurnNumber || 1,
      nextStarter: data.next_starter || null,
      allHandsEmpty: data.all_hands_empty || false,
      willContinue: data.will_continue || false
    };
    
    console.log(`🏆 TURN_COMPLETE_DEBUG: Transitioning to turn_results phase with state:`, {
      phase: newState.phase,
      turnWinner: newState.turnWinner,
      winningPlay: newState.winningPlay,
      playerPiles: newState.playerPiles,
      turnNumber: newState.turnNumber,
      nextStarter: newState.nextStarter
    });
    
    return newState;
  }

  /**
   * Handle score update event
   */
  private handleScoreUpdate(state: GameState, data: any): GameState {
    return {
      ...state,
      roundScores: data.round_scores || state.roundScores,
      totalScores: data.total_scores || state.totalScores
    };
  }

  /**
   * Handle round complete event
   */
  private handleRoundComplete(state: GameState, data: any): GameState {
    return {
      ...state,
      roundScores: data.round_scores || state.roundScores,
      totalScores: data.total_scores || state.totalScores,
      currentRound: state.currentRound + 1
    };
  }

  /**
   * Handle game ended event
   */
  private handleGameEnded(state: GameState, data: any): GameState {
    return {
      ...state,
      gameOver: true,
      winners: data.winners || [],
      totalScores: data.final_scores || state.totalScores
    };
  }

  /**
   * Update derived state (isMyTurn, allowedActions, etc.)
   */
  private updateDerivedState(state: GameState): GameState {
    const newState = { ...state };
    
    // Calculate isMyTurn
    newState.isMyTurn = this.calculateIsMyTurn(state);
    
    // Calculate allowed actions
    newState.allowedActions = this.calculateAllowedActions(state);
    
    // Calculate valid options
    newState.validOptions = this.calculateValidOptions(state);
    
    return newState;
  }

  /**
   * Calculate if it's the player's turn
   */
  private calculateIsMyTurn(state: GameState): boolean {
    switch (state.phase) {
      case 'preparation':
        return state.currentWeakPlayer === state.playerName;
        
      case 'declaration':
        return state.currentDeclarer === state.playerName;
        
      case 'turn': {
        // Check if it's specifically this player's turn
        const isMyTurnCalc = state.currentPlayer === state.playerName;
        console.log(`🎯 TURN_DEBUG: currentPlayer: ${state.currentPlayer}, playerName: ${state.playerName}, isMyTurn: ${isMyTurnCalc}`);
        console.log(`🎯 TURN_DEBUG: turnOrder:`, state.turnOrder);
        console.log(`🎯 TURN_DEBUG: currentTurnPlays:`, state.currentTurnPlays);
        return isMyTurnCalc;
      }
        
      case 'turn_results':
        return false; // No player-specific actions in turn results - everyone can continue
        
      case 'scoring':
        return false; // No player actions in scoring
        
      default:
        return false;
    }
  }

  /**
   * Calculate allowed actions for current state
   */
  private calculateAllowedActions(state: GameState): GameAction[] {
    const actions: GameAction[] = [];
    
    switch (state.phase) {
      case 'preparation':
        if (state.currentWeakPlayer === state.playerName) {
          actions.push('acceptRedeal', 'declineRedeal');
        }
        break;
        
      case 'declaration':
        if (state.currentDeclarer === state.playerName) {
          actions.push('makeDeclaration');
        }
        break;
        
      case 'turn':
        if (this.calculateIsMyTurn(state)) {
          actions.push('playPieces');
        }
        break;
        
      case 'turn_results':
        // No actions needed - backend auto-continues
        break;
        
      case 'scoring':
        if (state.gameOver) {
          actions.push('startNextRound');
        }
        break;
    }
    
    return actions;
  }

  /**
   * Calculate valid options for current state
   */
  private calculateValidOptions(state: GameState): number[] | number[][] {
    switch (state.phase) {
      case 'declaration':
        if (state.currentDeclarer === state.playerName) {
          return this.calculateValidDeclarations(state);
        }
        break;
        
      case 'turn':
        if (this.calculateIsMyTurn(state)) {
          return this.calculateValidPlays(state);
        }
        break;
    }
    
    return [];
  }

  /**
   * Calculate valid declaration values
   */
  private calculateValidDeclarations(state: GameState): number[] {
    const validValues: number[] = [];
    const currentTotal = (Object.values(state.declarations) as number[]).reduce((sum: number, val: number) => sum + val, 0);
    const declarationCount = Object.keys(state.declarations).length;
    const totalPlayers = state.players.length;
    const isLastPlayer = declarationCount === totalPlayers - 1;
    
    for (let value = 0; value <= 8; value++) {
      // Last player cannot make total equal 8
      if (isLastPlayer && currentTotal + value === 8) {
        continue;
      }
      validValues.push(value);
    }
    
    return validValues;
  }

  /**
   * Calculate valid piece plays
   */
  private calculateValidPlays(state: GameState): number[][] {
    if (!state.myHand || state.myHand.length === 0) {
      return [];
    }
    
    const validPlays: number[][] = [];
    const handSize = state.myHand.length;
    
    // If no required piece count, can play 1-6 pieces
    const minPieces = 1;
    const maxPieces = state.requiredPieceCount || Math.min(6, handSize);
    
    for (let count = minPieces; count <= maxPieces; count++) {
      // Generate combinations of indices
      const combinations = this.generateCombinations(handSize, count);
      validPlays.push(...combinations);
    }
    
    return validPlays;
  }

  /**
   * Generate combinations of indices
   */
  private generateCombinations(n: number, k: number): number[][] {
    const combinations: number[][] = [];
    
    function combine(start: number, current: number[]): void {
      if (current.length === k) {
        combinations.push([...current]);
        return;
      }
      
      for (let i = start; i < n; i++) {
        current.push(i);
        combine(i + 1, current);
        current.pop();
      }
    }
    
    combine(0, []);
    return combinations;
  }

  /**
   * Validate action is allowed
   */
  private validateAction(action: string, expectedPhase: string): void {
    if (this.isDestroyed) {
      throw new Error('GameService has been destroyed');
    }
    
    if (!this.state.isConnected) {
      throw new Error('Not connected to game');
    }
    
    if (this.state.phase !== expectedPhase) {
      throw new Error(`Cannot ${action} during ${this.state.phase} phase`);
    }
    
    if (this.state.error) {
      throw new Error(`Game error: ${this.state.error}`);
    }
  }

  /**
   * Send action to backend
   */
  private sendAction(event: string, data: Record<string, any>): void {
    if (!this.state.roomId) {
      throw new Error('No room connected');
    }
    
    const success = networkService.send(this.state.roomId, event, data);
    
    if (!success) {
      console.warn(`Action ${event} queued due to connection issue`);
    }
    
    console.log(`🎮 Action sent: ${event}`, data);
  }

  /**
   * Set state and notify listeners
   */
  private setState(newState: GameState, reason: string): void {
    const oldState = this.state;
    this.state = newState;
    
    // Add to event history
    const eventWithMeta: StateChangeEvent = {
      oldState: { ...oldState },
      newState: { ...newState },
      reason,
      sequence: ++this.sequenceNumber,
      timestamp: Date.now()
    };
    
    this.eventHistory.push(eventWithMeta);
    
    // Limit history size
    if (this.eventHistory.length > 1000) {
      this.eventHistory.shift();
    }
    
    // Update sequence in state
    this.state.lastEventSequence = this.sequenceNumber;
    
    // Debug logging
    console.group(`🎮 State Change: ${reason}`);
    console.log('Previous:', oldState);
    console.log('New:', newState);
    console.log('Diff:', this.stateDiff(oldState, newState));
    console.groupEnd();
    
    // Enable debugging
    if (typeof window !== 'undefined') {
      (window as any).__GAME_STATE_HISTORY__ = (window as any).__GAME_STATE_HISTORY__ || [];
      (window as any).__GAME_STATE_HISTORY__.push(eventWithMeta);
      
      // Limit window history
      if ((window as any).__GAME_STATE_HISTORY__.length > 100) {
        (window as any).__GAME_STATE_HISTORY__.shift();
      }
      
      // Debug helper
      (window as any).debugReplayToEvent = (sequence: number) => {
        this.replayToSequence(sequence);
      };
    }
    
    // Notify listeners
    this.notifyListeners();
  }

  /**
   * Apply event to state (pure function for replay)
   */
  private applyEvent(state: GameState, event: StateChangeEvent): GameState {
    return event.newState;
  }

  /**
   * Calculate state differences
   */
  private stateDiff(oldState: GameState, newState: GameState): Record<string, { from: any; to: any }> {
    const diff: Record<string, { from: any; to: any }> = {};
    
    for (const key in newState) {
      if (JSON.stringify(oldState[key as keyof GameState]) !== JSON.stringify(newState[key as keyof GameState])) {
        diff[key] = {
          from: oldState[key as keyof GameState],
          to: newState[key as keyof GameState]
        };
      }
    }
    
    return diff;
  }

  /**
   * Notify all listeners of state change
   */
  private notifyListeners(): void {
    const frozenState = this.getState();
    
    for (const listener of this.listeners) {
      try {
        listener(frozenState);
      } catch (error) {
        console.error('Listener error:', error);
      }
    }
    
    // Also emit as event
    this.dispatchEvent(new CustomEvent('stateChange', {
      detail: { state: frozenState }
    }));
  }

  /**
   * UI State Calculation Methods
   * These calculate derived state for UI components from backend data
   */

  /**
   * Calculate if hand is weak (no piece > 9 points)
   */
  private calculateWeakHand(hand: any[]): boolean {
    if (!hand || hand.length === 0) return false;
    return hand.every(piece => (piece.value || piece.point || 0) <= 9);
  }

  /**
   * Calculate total hand value
   */
  private calculateHandValue(hand: any[]): number {
    if (!hand || hand.length === 0) return 0;
    return hand.reduce((sum, piece) => sum + (piece.value || piece.point || 0), 0);
  }

  /**
   * Calculate highest card value in hand
   */
  private calculateHighestCardValue(hand: any[]): number {
    if (!hand || hand.length === 0) return 0;
    return Math.max(...hand.map(piece => piece.value || piece.point || 0));
  }

  /**
   * Calculate estimated piles from hand strength
   */
  private calculateEstimatedPiles(hand: any[]): number {
    if (!hand || hand.length === 0) return 0;
    
    const values = hand.map(piece => piece.value || piece.point || 0);
    const averageValue = values.reduce((sum, val) => sum + val, 0) / values.length;
    const highCards = values.filter(val => val > 10).length;
    
    // Rough estimation: more high cards = more potential piles
    return Math.max(0, Math.min(8, Math.floor(averageValue / 4) + highCards));
  }

  /**
   * Calculate hand strength score
   */
  private calculateHandStrength(hand: any[]): number {
    if (!hand || hand.length === 0) return 0;
    
    const values = hand.map(piece => piece.value || piece.point || 0);
    const averageValue = values.reduce((sum, val) => sum + val, 0) / values.length;
    const maxValue = Math.max(...values);
    
    // Normalize to 0-100 scale
    return Math.min(100, Math.round((averageValue * 2) + (maxValue / 2)));
  }

  /**
   * Calculate players with scores for scoring phase
   */
  private calculatePlayersWithScores(
    players: any[], 
    roundScores: Record<string, any>, // Changed from number to any to handle backend objects
    totalScores: Record<string, number>,
    redealMultiplier: number,
    winners: string[]
  ): any[] {
    return players.map(player => {
      // Handle backend scoring objects vs simple numbers
      const playerRoundScore = roundScores[player.name];
      const roundScore = (typeof playerRoundScore === 'object' && playerRoundScore?.final_score !== undefined) 
        ? playerRoundScore.final_score 
        : (playerRoundScore || 0);
      
      const baseScore = (typeof playerRoundScore === 'object' && playerRoundScore?.base_score !== undefined)
        ? playerRoundScore.base_score
        : Math.round(roundScore / Math.max(1, redealMultiplier));
      
      const actualPiles = (typeof playerRoundScore === 'object' && playerRoundScore?.actual !== undefined)
        ? playerRoundScore.actual
        : this.deriveActualPiles(player, roundScore);
      
      const declaredPiles = (typeof playerRoundScore === 'object' && playerRoundScore?.declared !== undefined)
        ? playerRoundScore.declared
        : (player.pile_count || 0);
      
      const totalScore = (typeof playerRoundScore === 'object' && playerRoundScore?.total_score !== undefined)
        ? playerRoundScore.total_score
        : (totalScores[player.name] || 0);
      
      return {
        ...player,
        roundScore,
        totalScore,
        baseScore,
        actualPiles,
        pile_count: declaredPiles,  // Add declared value for ScoringUI
        scoreExplanation: this.generateScoreExplanation(player, roundScore, redealMultiplier),
        isWinner: winners.includes(player.name)
      };
    }).sort((a, b) => b.totalScore - a.totalScore);
  }

  /**
   * Derive actual piles from score (best effort)
   */
  private deriveActualPiles(player: any, roundScore: number): number | string {
    const declared = player.pile_count || 0;
    
    if (declared === 0 && roundScore === 3) return 0; // Perfect zero
    if (declared === 0 && roundScore < 0) return Math.abs(roundScore); // Broke zero
    if (roundScore === declared + 5) return declared; // Perfect match
    
    return '?'; // Cannot determine
  }

  /**
   * Generate score explanation text
   */
  private generateScoreExplanation(player: any, roundScore: number, redealMultiplier: number): string {
    const declared = player.pile_count || 0;
    const baseScore = Math.round(roundScore / Math.max(1, redealMultiplier));
    
    let explanation = '';
    
    if (declared === 0 && baseScore === 3) {
      explanation = 'Perfect zero prediction bonus';
    } else if (declared === 0 && baseScore < 0) {
      explanation = 'Penalty for breaking zero declaration';
    } else if (baseScore === declared + 5) {
      explanation = 'Perfect prediction bonus';
    } else if (baseScore < 0) {
      explanation = 'Penalty for missing target';
    } else {
      explanation = 'Score calculation applied';
    }
    
    if (redealMultiplier > 1) {
      explanation += ` (×${redealMultiplier} redeal multiplier)`;
    }
    
    return explanation;
  }
}

// Export singleton instance for immediate use
export const gameService = GameService.getInstance();

// Also export the class for testing purposes
export default GameService;