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
import { storeSession, clearSession } from '../utils/sessionStorage';
import type {
  GameState,
  PhaseData,
  StateChangeEvent,
  GameEventType,
  GameAction,
  StateListener,
  CleanupFunction,
  NetworkEventDetail,
} from './types';
import { parsePieces } from '../utils/pieceParser';

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
      throw new Error(
        'GameService is a singleton. Use GameService.getInstance()'
      );
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
      // Set room ID and player name immediately so events can be processed
      this.setState(
        {
          ...this.state,
          roomId,
          playerName,
        },
        'JOIN_ROOM_INIT'
      );

      // Connect to room via NetworkService
      await networkService.connectToRoom(roomId, { playerName });

      // Update connection state
      this.setState(
        {
          ...this.state,
          isConnected: true,
          error: null,
          gameStartTime: Date.now(),
        },
        'JOIN_ROOM_CONNECTED'
      );

      // Store session for reconnection after browser close/refresh
      const sessionId = `${roomId}-${playerName}-${Date.now()}`;
      storeSession(roomId, playerName, sessionId, this.state.phase);

      console.log(`🎮 GameService: Joined room ${roomId} as ${playerName}`);
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Unknown error';
      this.setState(
        {
          ...this.state,
          error: `Failed to join room: ${errorMessage}`,
          isConnected: false,
        },
        'JOIN_ROOM_FAILED'
      );

      throw error;
    }
  }

  /**
   * Leave current room
   */
  async leaveRoom(): Promise<void> {
    if (this.state.roomId) {
      await networkService.disconnectFromRoom(this.state.roomId);

      // 🎯 FIX: Check if this is an active game state that should be preserved
      const hasActiveGameState = this.state.phase !== 'waiting' && 
                                 this.state.currentRound > 0;
      
      console.log('🎮 GameService: Leaving room, preserving game state:', {
        hasActiveGameState,
        currentPhase: this.state.phase,
        currentRound: this.state.currentRound
      });

      if (hasActiveGameState) {
        // Preserve game state during temporary disconnection/reconnection
        this.setState(
          {
            ...this.state,
            isConnected: false,
            error: null,
          },
          'LEAVE_ROOM'
        );
        
        console.log('🎮 GameService: Left room while preserving active game state');
      } else {
        // Clear session storage only when truly leaving (not reconnecting)
        clearSession();

        this.setState(
          {
            ...this.getInitialState(),
            playerName: this.state.playerName, // Preserve player name
          },
          'LEAVE_ROOM'
        );

        console.log('🎮 GameService: Left room and reset to initial state');
      }
    }
  }

  // ===== GAME ACTIONS =====

  /**
   * Accept redeal during preparation phase
   */
  acceptRedeal(): void {
    this.validateAction('ACCEPT_REDEAL', 'preparation');
    this.sendAction('accept_redeal', { player_name: this.state.playerName });
  }

  /**
   * Decline redeal during preparation phase
   */
  declineRedeal(): void {
    this.validateAction('DECLINE_REDEAL', 'preparation');
    this.sendAction('decline_redeal', { player_name: this.state.playerName });
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
      const currentTotal = (
        Object.values(this.state.declarations) as number[]
      ).reduce((sum: number, val: number) => sum + val, 0);
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

    if (indices.some((i) => i < 0 || i >= this.state.myHand.length)) {
      throw new Error('Invalid piece indices');
    }

    // Check if it's player's turn
    if (!this.state.isMyTurn) {
      throw new Error('Not your turn to play');
    }

    // Validate piece count matches required (if set)
    if (
      this.state.requiredPieceCount !== null &&
      indices.length !== this.state.requiredPieceCount
    ) {
      throw new Error(
        `Must play exactly ${this.state.requiredPieceCount} pieces`
      );
    }

    // Calculate total value of selected pieces
    const selectedPieces = indices.map((i) => this.state.myHand[i]);
    const totalValue = selectedPieces.reduce(
      (sum, piece) => sum + (piece.value || 0),
      0
    );

    this.sendAction('play', {
      piece_indices: indices,
      player_name: this.state.playerName,
      play_value: totalValue,
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
    const eventsToReplay = this.eventHistory.filter(
      (e) => e.sequence <= targetSequence
    );

    this.state = eventsToReplay.reduce(
      (state, event) => this.applyEvent(state, event),
      initialState
    );

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

    // Clear session storage when destroying service
    clearSession();

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
      currentRound: 1,
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

      // Connection/Disconnect state
      disconnectedPlayers: [],
      host: null,

      // UI state
      isMyTurn: false,
      allowedActions: [],
      validOptions: [],

      // Meta state
      lastEventSequence: 0,
      error: null,
      gameOver: false,
      gameStartTime: null,
    };
  }

  /**
   * Set up network event listeners
   */
  private setupNetworkListeners(): void {
    // Connection events
    networkService.addEventListener(
      'connected',
      this.handleNetworkConnection.bind(this)
    );
    networkService.addEventListener(
      'disconnected',
      this.handleNetworkDisconnection.bind(this)
    );

    // Game events
    const gameEvents: GameEventType[] = [
      'game_started',
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
      'game_ended',
      'player_disconnected',
      'player_reconnected',
      'host_changed',
    ];

    // Special error events
    networkService.addEventListener(
      'room_not_found',
      this.handleRoomNotFound.bind(this)
    );

    gameEvents.forEach((event) => {
      networkService.addEventListener(
        event,
        this.handleNetworkEvent.bind(this)
      );
    });
  }

  /**
   * Handle network connection
   */
  private handleNetworkConnection(): void {
    // Connection established - update state

    this.setState(
      {
        ...this.state,
        isConnected: true,
        error: null,
      },
      'NETWORK_CONNECTED'
    );
  }

  /**
   * Handle network disconnection
   */
  private handleNetworkDisconnection(event: Event): void {
    const customEvent = event as CustomEvent<{ intentional: boolean }>;
    const { intentional } = customEvent.detail;

    this.setState(
      {
        ...this.state,
        isConnected: false,
        error: intentional ? null : 'Connection lost',
      },
      'NETWORK_DISCONNECTED'
    );
  }

  /**
   * Handle room not found event
   */
  private handleRoomNotFound(event: Event): void {
    const customEvent = event as CustomEvent<NetworkEventDetail>;
    const { data } = customEvent.detail;

    console.log('🚫 Room not found:', data);

    // Clear the invalid session
    import('../utils/sessionStorage').then(({ clearSession }) => {
      clearSession();
    });

    // Show error message to user
    const message = data?.message || 'This game room no longer exists';
    const suggestion = data?.suggestion || 'Please return to the start page';

    // Update state with error
    this.setState(
      {
        ...this.state,
        error: `${message}. ${suggestion}`,
        phase: 'waiting' as const,
      },
      'ROOM_NOT_FOUND'
    );

    // Show toast if available
    if (typeof window !== 'undefined' && (window as any).showToast) {
      (window as any).showToast({
        type: 'error',
        title: 'Room Not Found',
        message: `${message}. ${suggestion}`,
        duration: 8000,
      });
    }

    // Navigate to start page after delay
    setTimeout(() => {
      if (typeof window !== 'undefined') {
        window.location.href = '/';
      }
    }, 3000);
  }

  /**
   * Handle network events
   */
  private handleNetworkEvent(event: Event): void {
    const customEvent = event as CustomEvent<NetworkEventDetail>;
    const { roomId, data } = customEvent.detail;

    console.log(`🔍 [DEBUG] GameService received network event: ${event.type}`, {
      eventType: event.type,
      roomId,
      currentRoomId: this.state.roomId,
      data
    });

    // Only process events for our room
    if (roomId !== this.state.roomId) {
      console.log(`🔍 [DEBUG] Ignoring event - room mismatch: ${roomId} !== ${this.state.roomId}`);
      return;
    }

    try {
      console.log(`🔍 [DEBUG] Processing game event: ${event.type}`);
      const newState = this.processGameEvent(event.type, data);
      this.setState(newState, `NETWORK_EVENT:${event.type.toUpperCase()}`);
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Unknown error';
      console.error(`Failed to process ${event.type} event:`, error);
      this.setState(
        {
          ...this.state,
          error: `Event processing error: ${errorMessage}`,
        },
        'EVENT_ERROR'
      );
    }
  }

  /**
   * Process game events from backend
   */
  private processGameEvent(eventType: string, data: any): GameState {
    console.log(`🔍 [DEBUG] processGameEvent called with eventType: ${eventType}`, data);
    let newState = { ...this.state };

    switch (eventType) {
      case 'game_started':
        console.log(`🔍 [DEBUG] Calling handleGameStarted`);
        newState = this.handleGameStarted(newState, data);
        break;

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
        newState = this.handlePlay(newState, data);
        break;

      case 'turn_resolved':
        newState = this.handleTurnResolved(newState, data);
        break;

      case 'turn_complete':
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

      case 'player_disconnected':
        newState = this.handlePlayerDisconnected(newState, data);
        break;

      case 'player_reconnected':
        newState = this.handlePlayerReconnected(newState, data);
        break;

      case 'host_changed':
        newState = this.handleHostChanged(newState, data);
        break;

      case 'play_rejected': {
        const message =
          data.details || data.message || 'Invalid play. Please try again.';
        alert(message);
        // Keep play UI active for retry
        break;
      }

      case 'critical_error':
        alert(
          data.message ||
            'Game ended due to critical error. Returning to lobby...'
        );
        window.location.href = '/lobby';
        break;

      default:
        console.warn(`Unknown game event: ${eventType}`, data);
        return newState;
    }

    // Update derived state
    newState = this.updateDerivedState(newState);

    return newState;
  }

  /**
   * Handle phase change events
   */
  private handlePhaseChange(state: GameState, data: any): GameState {
    const newState = { ...state };

    // 🎯 FIX: Normalize phase to lowercase to match frontend expectations
    newState.phase = data.phase ? data.phase.toLowerCase() : 'waiting';
    newState.currentRound = data.round || state.currentRound;

    // Extract my hand from players data (sent by backend)
    if (data.players && state.playerName && data.players[state.playerName]) {
      const myPlayerData = data.players[state.playerName];
      if (myPlayerData.hand) {
        // Convert string pieces back to objects for frontend with original indices
        const unsortedHand = myPlayerData.hand.map(
          (pieceStr: string, index: number) => {
            // Parse piece strings like "ELEPHANT_RED(10)" into objects
            const match = pieceStr.match(/^(.+)\((\d+)\)$/);
            if (match) {
              const [, name, value] = match;
              const [piece, color] = name.split('_');
              return {
                kind: piece, // Keep uppercase "GENERAL"
                color: color.toLowerCase() as 'red' | 'black', // Convert to lowercase for type compatibility
                value: parseInt(value),
                displayName: `${piece} ${color}`,
                originalIndex: index, // Store the original index before sorting
              };
            }
            return {
              kind: 'UNKNOWN',
              color: 'red' as 'red' | 'black', // Default to red for unknown pieces
              value: 0,
              displayName: pieceStr,
              originalIndex: index, // Store the original index before sorting
            };
          }
        );

        // Sort myHand by color (red first) then by value (high to low)

        newState.myHand = [...unsortedHand].sort((a, b) => {
          // First sort by color: red comes before black
          if (a.color === 'red' && b.color !== 'red') return -1;
          if (a.color !== 'red' && b.color === 'red') return 1;
          // Then sort by value (high to low)
          return (b.value || 0) - (a.value || 0);
        });
      }
    }

    // Convert players data to array for UI components (handle both array and object formats)
    if (data.players) {
      if (Array.isArray(data.players)) {
        // Players data is already an array
        newState.players = data.players.map((playerData: any) => ({
          name: playerData.name,
          score: playerData.score || 0,
          is_bot: playerData.is_bot || false,
          is_host: playerData.is_host || false,
          avatar_color: playerData.avatar_color || null,
          zero_declares_in_a_row: playerData.zero_declares_in_a_row || 0,
          hand_size: playerData.hand_size || 0,
          captured_piles: playerData.captured_piles || 0,
          declared: playerData.declared || 0,
        }));
      } else if (typeof data.players === 'object' && data.players !== null) {
        // Players data is a dictionary/object - convert to array
        newState.players = Object.entries(data.players).map(
          ([playerName, playerData]: [string, any]) => ({
            name: playerName, // Use the key as the name
            score: playerData.score || 0,
            is_bot: playerData.is_bot || false,
            is_host: playerData.is_host || false,
            avatar_color: playerData.avatar_color || null,
            zero_declares_in_a_row: playerData.zero_declares_in_a_row || 0,
            hand_size: playerData.hand_size || 0,
            captured_piles: playerData.captured_piles || 0,
            declared: playerData.declared || 0,
          })
        );
      } else {
        console.warn('🚫 [GameService] data.players is neither array nor object:', typeof data.players, data.players);
      }
    }

    // Extract phase-specific data
    if (data.phase_data) {
      const phaseData: PhaseData = data.phase_data;

      // Update players list (prefer backend phase_data over data.players for player metadata)
      if (phaseData.players && Array.isArray(phaseData.players)) {
        // Merge phase_data players with existing player data to preserve zero_declares_in_a_row
        const existingPlayersMap = new Map(
          newState.players.map((p) => [p.name, p])
        );
        newState.players = phaseData.players.map((player: any) => {
          const existing = existingPlayersMap.get(player.name);
          return {
            ...player,
            avatar_color: player.avatar_color,
            zero_declares_in_a_row: existing?.zero_declares_in_a_row || 0,
            // Preserve connection status if not provided by backend
            is_connected:
              player.is_connected !== undefined
                ? player.is_connected
                : existing?.is_connected,
            disconnect_time:
              player.disconnect_time || existing?.disconnect_time,
            original_is_bot:
              player.original_is_bot !== undefined
                ? player.original_is_bot
                : existing?.original_is_bot,
          };
        });

        // Update disconnected players list based on player states
        newState.disconnectedPlayers = newState.players
          .filter((p) => p.is_bot && p.original_is_bot === false)
          .map((p) => p.name);
      } else if (phaseData.players) {
        console.warn('🚫 [GameService] phaseData.players is not an array:', typeof phaseData.players, phaseData.players);
      }

      // Phase-specific updates
      switch (data.phase) {
        case 'preparation':
          // Fallback to phase_data.my_hand if data.players doesn't have it
          if (phaseData.my_hand && !newState.myHand.length) {
            newState.myHand = phaseData.my_hand;
            // Sort myHand by color (red first) then by value (high to low)

            newState.myHand.sort((a, b) => {
              // First sort by color: red comes before black
              if (a.color === 'red' && b.color !== 'red') return -1;
              if (a.color !== 'red' && b.color === 'red') return 1;
              // Then sort by value (high to low)
              return (b.value || 0) - (a.value || 0);
            });
          }
          if (phaseData.round_starter)
            newState.roundStarter = phaseData.round_starter;
          newState.redealMultiplier = phaseData.redeal_multiplier || 1;
          if (phaseData.weak_hands) newState.weakHands = phaseData.weak_hands;
          if (phaseData.current_weak_player)
            newState.currentWeakPlayer = phaseData.current_weak_player;

          // Extract simultaneous mode fields
          newState.simultaneousMode = phaseData.simultaneous_mode || false;
          newState.weakPlayersAwaiting = phaseData.weak_players_awaiting || [];
          newState.decisionsReceived = phaseData.decisions_received || 0;
          newState.decisionsNeeded = phaseData.decisions_needed || 0;

          // Extract dealing cards flag
          if (phaseData.dealing_cards !== undefined) {
            newState.dealingCards = phaseData.dealing_cards;
          }

          // Calculate preparation-specific UI state
          if (newState.myHand.length > 0) {
            newState.isMyHandWeak = this.calculateWeakHand(newState.myHand);
            newState.handValue = this.calculateHandValue(newState.myHand);
            newState.highestCardValue = this.calculateHighestCardValue(
              newState.myHand
            );
          }

          // Determine if it's my decision (works for both sequential and simultaneous modes)
          if (newState.simultaneousMode && newState.playerName) {
            // In simultaneous mode, check if I'm in weak_players_awaiting
            newState.isMyDecision = newState.weakPlayersAwaiting.includes(
              newState.playerName
            );
          } else if (phaseData.current_weak_player && newState.playerName) {
            // In sequential mode, check if I'm the current weak player
            newState.isMyDecision =
              phaseData.current_weak_player === newState.playerName;
          }
          break;

        case 'round_start':
          // Extract round start specific data
          if (phaseData.current_starter) {
            newState.currentStarter = phaseData.current_starter;
          }
          if (phaseData.starter_reason) {
            newState.starterReason = phaseData.starter_reason;
          }
          break;

        case 'declaration':
          // Fallback to phase_data.my_hand if data.players doesn't have it
          if (phaseData.my_hand && !newState.myHand.length) {
            newState.myHand = phaseData.my_hand;
            // Sort myHand by color (red first) then by value (high to low)

            newState.myHand.sort((a, b) => {
              // First sort by color: red comes before black
              if (a.color === 'red' && b.color !== 'red') return -1;
              if (a.color !== 'red' && b.color === 'red') return 1;
              // Then sort by value (high to low)
              return (b.value || 0) - (a.value || 0);
            });
          }
          if (phaseData.declaration_order)
            newState.declarationOrder = phaseData.declaration_order;
          if (phaseData.current_declarer)
            newState.currentDeclarer = phaseData.current_declarer;
          newState.declarations = phaseData.declarations || {};

          // Calculate declaration-specific UI state
          // Use backend's calculated values first, fallback to frontend calculation
          newState.currentTotal =
            phaseData.declaration_total ??
            Object.values(phaseData.declarations || {}).reduce(
              (sum: number, val: number) => sum + val,
              0
            );

          if (phaseData.declaration_order) {
            newState.declarationProgress = {
              declared: Object.keys(phaseData.declarations || {}).length,
              total: phaseData.declaration_order.length,
            };
            newState.isLastPlayer =
              Object.keys(phaseData.declarations || {}).length ===
              phaseData.declaration_order.length - 1;
          } else if (phaseData.players) {
            newState.declarationProgress = {
              declared: Object.keys(phaseData.declarations || {}).length,
              total: phaseData.players.length,
            };
            newState.isLastPlayer =
              Object.keys(phaseData.declarations || {}).length ===
              phaseData.players.length - 1;
          }
          if (newState.myHand.length > 0) {
            newState.estimatedPiles = this.calculateEstimatedPiles(
              newState.myHand
            );
            newState.handStrength = this.calculateHandStrength(newState.myHand);
          }
          break;

        case 'turn':
          if (phaseData.turn_order) newState.turnOrder = phaseData.turn_order;
          if (phaseData.current_turn_starter)
            newState.currentTurnStarter = phaseData.current_turn_starter;
          if (phaseData.current_player)
            newState.currentPlayer = phaseData.current_player;

          // Use backend's required_piece_count as single source of truth
          if (phaseData.required_piece_count !== undefined) {
            newState.requiredPieceCount = phaseData.required_piece_count;
          }

          // Get accumulated pile counts from backend
          if (phaseData.pile_counts !== undefined) {
            newState.pileCounts = phaseData.pile_counts;
          }

          // Convert backend's turn_plays dictionary to frontend's currentTurnPlays array
          if (phaseData.turn_plays !== undefined) {
            // Check if turn_plays is an empty object or array
            if (
              typeof phaseData.turn_plays === 'object' &&
              Object.keys(phaseData.turn_plays).length === 0
            ) {
              newState.currentTurnPlays = [];
            } else if (
              phaseData.turn_plays &&
              typeof phaseData.turn_plays === 'object'
            ) {
              newState.currentTurnPlays = Object.entries(
                phaseData.turn_plays
              ).map(([playerName, playData]: [string, any]) => {
                const playType =
                  playData.type || playData.play_type || 'UNKNOWN';
                // A play is invalid if explicitly marked as invalid OR if play_type is 'INVALID'
                const isValid =
                  playData.is_valid !== false && playType !== 'INVALID';

                return {
                  player: playerName,
                  pieces: parsePieces(playData.pieces || []),
                  isValid,
                  playType,
                  totalValue: playData.play_value || 0,
                };
              });
            }
          } else {
            // Parse pieces in current_turn_plays array format
            newState.currentTurnPlays = (
              phaseData.current_turn_plays || []
            ).map((play: any) => ({
              ...play,
              pieces: parsePieces(play.pieces || play.cards || []),
            }));
          }

          newState.currentTurnNumber = phaseData.current_turn_number || 0;

          // Calculate turn-specific UI state
          newState.canPlayAnyCount =
            !newState.requiredPieceCount && newState.isMyTurn;
          newState.selectedPlayValue = 0; // Will be updated when player selects pieces
          break;

        case 'scoring': {
          // Process backend scoring objects to extract numeric values
          const processedRoundScores: Record<string, number> = {};
          const rawRoundScores = phaseData.round_scores || {};

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

          // Calculate scoring-specific UI state
          if (
            phaseData.scoring_players_data &&
            phaseData.round_scores &&
            phaseData.total_scores
          ) {
            newState.playersWithScores = this.calculatePlayersWithScores(
              phaseData.scoring_players_data,
              phaseData.round_scores,
              phaseData.total_scores,
              phaseData.redeal_multiplier || 1,
              phaseData.winners || []
            );
          } else {
            // Fallback: try to use newState.players if phaseData.scoring_players_data is missing
            if (
              !phaseData.scoring_players_data &&
              newState.players &&
              newState.players.length > 0
            ) {
              if (phaseData.round_scores && phaseData.total_scores) {
                newState.playersWithScores = this.calculatePlayersWithScores(
                  newState.players,
                  phaseData.round_scores,
                  phaseData.total_scores,
                  phaseData.redeal_multiplier || 1,
                  phaseData.winners || []
                );
              }
            }
          }
          break;
        }

        case 'game_over':
          // Handle game over phase
          newState.gameOver = true;
          if (phaseData.winners) {
            newState.winners = phaseData.winners;
          }
          if (phaseData.final_rankings) {
            newState.final_rankings = phaseData.final_rankings;
          }
          if (phaseData.game_stats) {
            newState.game_stats = phaseData.game_stats;
          }
          break;
      }
    }

    // Clear error on successful phase change
    newState.error = null;

    // Update session storage with new phase
    if (state.roomId && state.playerName) {
      const sessionId = `${state.roomId}-${state.playerName}-${Date.now()}`;
      storeSession(state.roomId, state.playerName, sessionId, newState.phase);
    }

    return newState;
  }

  /**
   * Handle game started event
   */
  private handleGameStarted(state: GameState, data: any): GameState {
    console.log('🎮 GameService.handleGameStarted: START');
    console.log('🎮 GameService.handleGameStarted: Previous state:', {
      phase: state.phase,
      isConnected: state.isConnected,
      roomId: state.roomId,
      playerName: state.playerName,
      myHandLength: state.myHand?.length
    });
    console.log('🎮 GameService.handleGameStarted: Event data:', data);
    
    const newState = { ...state };
    
    // Basic game initialization - detailed state will come from phase_change events
    newState.currentRound = data.round_number || data.round || 1;
    
    // Update players list if provided (as simple array of names)
    if (data.players && Array.isArray(data.players)) {
      console.log('🎮 GameService.handleGameStarted: Updating players list:', data.players);
      newState.players = data.players.map((playerName: string, index: number) => ({
        name: playerName,
        score: 0,
        is_bot: false, // Will be updated by phase_change events
        is_host: false, // Will be updated by phase_change events
        avatar_color: null,
        zero_declares_in_a_row: 0,
        hand_size: 8, // Default initial hand size
        captured_piles: 0,
        declared: 0,
      }));
    }
    
    // 🎯 FIX: Set phase to a transitional state so GamePage shows proper loading instead of stuck "waiting"
    // This prevents the "stuck on waiting page" issue after game start
    const previousPhase = newState.phase;
    newState.phase = 'preparation'; // Start with preparation phase as default, will be updated by phase_change event
    
    // Clear any previous error state since game is starting
    newState.error = null;
    
    console.log(`🎮 GameService.handleGameStarted: Phase transition: ${previousPhase} → ${newState.phase}`);
    console.log(`🎮 GameService.handleGameStarted: Game initialized - Round: ${newState.currentRound}, Players: ${data.players?.length || 0}`);
    console.log('🎮 GameService.handleGameStarted: New state summary:', {
      phase: newState.phase,
      currentRound: newState.currentRound,
      playersCount: newState.players?.length,
      myHandLength: newState.myHand?.length,
      isConnected: newState.isConnected
    });
    
    // Notify listeners about state change
    console.log('🎮 GameService.handleGameStarted: About to notify listeners of state change');
    
    // Store the new state before returning
    console.log('🎮 GameService.handleGameStarted: COMPLETE - returning new state');
    return newState;
  }

  /**
   * Handle weak hands found event
   */
  private handleWeakHandsFound(state: GameState, data: any): GameState {
    return {
      ...state,
      weakHands: data.weak_hands || [],
      currentWeakPlayer: data.current_weak_player || null,
    };
  }

  /**
   * Handle redeal decision needed event
   */
  private handleRedealDecisionNeeded(state: GameState, data: any): GameState {
    return {
      ...state,
      currentWeakPlayer: data.player,
    };
  }

  /**
   * Handle redeal executed event
   */
  private handleRedealExecuted(state: GameState, data: any): GameState {
    const newHand = data.my_hand || state.myHand;
    // Sort myHand by color (red first) then by value (high to low)
    if (Array.isArray(newHand)) {
      newHand.sort((a, b) => {
        // First sort by color: red comes before black
        if (a.color === 'red' && b.color !== 'red') return -1;
        if (a.color !== 'red' && b.color === 'red') return 1;
        // Then sort by value (high to low)
        return (b.value || 0) - (a.value || 0);
      });
    }

    return {
      ...state,
      myHand: newHand,
      redealMultiplier: data.redeal_multiplier || state.redealMultiplier,
      weakHands: [],
      currentWeakPlayer: null,
      redealRequests: {},
    };
  }

  /**
   * Handle declare event
   */
  private handleDeclare(state: GameState, data: any): GameState {
    const newDeclarations = {
      ...state.declarations,
      [data.player]: data.value,
    };

    const declarationTotal = (
      Object.values(newDeclarations) as number[]
    ).reduce((sum: number, val: number) => sum + val, 0);

    // Find next declarer
    const currentIndex = state.declarationOrder.indexOf(data.player);
    const nextIndex = currentIndex + 1;
    const nextDeclarer =
      nextIndex < state.declarationOrder.length
        ? state.declarationOrder[nextIndex]
        : null;

    // Calculate derived state for declaration phase
    const newState = {
      ...state,
      declarations: newDeclarations,
      declarationTotal,
      currentDeclarer: nextDeclarer,
      currentTotal: declarationTotal, // Add this for UI
    };

    // Update declaration progress - use declarationOrder length if players not available
    const totalPlayers =
      state.players && state.players.length > 0
        ? state.players.length
        : state.declarationOrder && state.declarationOrder.length > 0
          ? state.declarationOrder.length
          : 4; // fallback to 4 players

    newState.declarationProgress = {
      declared: Object.keys(newDeclarations).length,
      total: totalPlayers,
    };

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

    // 🚀 ENTERPRISE: With enterprise architecture, phase_change events contain complete turn_plays data
    // Individual play events are only used for immediate UI feedback, phase_change has authoritative data

    // Check if we need to transition from turn_results back to turn phase
    let newPhase = state.phase;

    if (state.phase === 'turn_results') {
      // We're getting a play event while in turn_results, this means a new turn has started
      newPhase = 'turn';
    }

    // Transform backend data structure to frontend format for immediate feedback
    const playData = {
      player: data.player,
      cards: data.pieces || [], // Backend sends 'pieces', frontend expects 'cards'
      isValid: data.is_valid,
      playType: data.play_type,
      totalValue: data.play_value || 0,
    };

    // Note: We don't update currentTurnPlays here anymore since enterprise phase_change events
    // contain the authoritative turn_plays data. This prevents conflicts and ensures consistency.

    // 🚀 ENTERPRISE FIX: Don't set requiredPieceCount from play events
    // The backend phase_change events contain the authoritative required_piece_count
    // Setting it here from play events can cause stale data conflicts

    // Reset required piece count when starting new turn
    let requiredPieceCount = state.requiredPieceCount;
    if (newPhase === 'turn' && state.phase === 'turn_results') {
      requiredPieceCount = null;
    }

    // Update current player from the play event
    let newCurrentPlayer = state.currentPlayer;
    if (data.next_player) {
      newCurrentPlayer = data.next_player;
    } else if (data.turn_complete) {
      // Turn complete - next player will be set
    }

    // Check if turn is complete
    if (data.turn_complete) {
      // Turn complete logic handled by phase_change events
    }

    return {
      ...state,
      phase: newPhase,
      // Don't override currentTurnPlays - let phase_change events be authoritative
      // currentTurnPlays: managed by phase_change events in enterprise architecture
      requiredPieceCount,
      currentPlayer: newCurrentPlayer,
      // Clear turn results data when transitioning to new turn
      ...(newPhase === 'turn' && state.phase === 'turn_results'
        ? {
            turnWinner: null,
            winningPlay: null,
            currentTurnPlays: [], // Clear turn plays when transitioning to new turn
          }
        : {}),
    };
  }

  /**
   * Handle turn resolved event
   */
  private handleTurnResolved(state: GameState, data: any): GameState {
    const newHand = data.my_hand || state.myHand;
    // Sort myHand by color (red first) then by value (high to low)
    if (Array.isArray(newHand)) {
      newHand.sort((a, b) => {
        // First sort by color: red comes before black
        if (a.color === 'red' && b.color !== 'red') return -1;
        if (a.color !== 'red' && b.color === 'red') return 1;
        // Then sort by value (high to low)
        return (b.value || 0) - (a.value || 0);
      });
    }

    return {
      ...state,
      currentTurnPlays: [],
      requiredPieceCount: null,
      myHand: newHand,
      currentTurnNumber: state.currentTurnNumber + 1,
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

    const newState = {
      ...state,
      phase: 'turn_results' as const,
      turnWinner: data.winner || null,
      winningPlay: data.winning_play || null,
      playerPiles: data.player_piles || {},
      players: data.turn_players_data || state.players, // Update players with captured_piles and declared
      turnNumber: data.turn_number || state.currentTurnNumber || 1,
      nextStarter: data.next_starter || null,
      allHandsEmpty: data.all_hands_empty || false,
      willContinue: data.will_continue || false,
    };

    return newState;
  }

  /**
   * Handle score update event
   */
  private handleScoreUpdate(state: GameState, data: any): GameState {
    return {
      ...state,
      roundScores: data.round_scores || state.roundScores,
      totalScores: data.total_scores || state.totalScores,
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
      currentRound: state.currentRound + 1,
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
      totalScores: data.final_scores || state.totalScores,
    };
  }

  /**
   * Handle player disconnected event
   */
  private handlePlayerDisconnected(state: GameState, data: any): GameState {
    const newState = { ...state };

    // Add to disconnected players list
    if (
      data.player_name &&
      !newState.disconnectedPlayers.includes(data.player_name)
    ) {
      newState.disconnectedPlayers = [
        ...newState.disconnectedPlayers,
        data.player_name,
      ];
    }

    // Update player data if available
    if (data.player_name && state.players) {
      newState.players = state.players.map((player) => {
        if (player.name === data.player_name) {
          return {
            ...player,
            is_bot: data.is_bot !== undefined ? data.is_bot : true,
            is_connected: false,
            disconnect_time: data.disconnect_time || new Date().toISOString(),
          };
        }
        return player;
      });
    }

    return newState;
  }

  /**
   * Handle player reconnected event
   */
  private handlePlayerReconnected(state: GameState, data: any): GameState {
    const newState = { ...state };

    // Remove from disconnected players list
    if (data.player_name) {
      newState.disconnectedPlayers = newState.disconnectedPlayers.filter(
        (name) => name !== data.player_name
      );
    }

    // Update player data
    if (data.player_name && state.players) {
      newState.players = state.players.map((player) => {
        if (player.name === data.player_name) {
          return {
            ...player,
            is_bot:
              data.original_is_bot !== undefined ? data.original_is_bot : false,
            is_connected: true,
            disconnect_time: undefined,
          };
        }
        return player;
      });
    }

    return newState;
  }

  /**
   * Handle host changed event
   */
  private handleHostChanged(state: GameState, data: any): GameState {
    return {
      ...state,
      host: data.new_host || null,
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
    const currentTotal = (Object.values(state.declarations) as number[]).reduce(
      (sum: number, val: number) => sum + val,
      0
    );
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
      timestamp: Date.now(),
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
      (window as any).__GAME_STATE_HISTORY__ =
        (window as any).__GAME_STATE_HISTORY__ || [];
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
  private stateDiff(
    oldState: GameState,
    newState: GameState
  ): Record<string, { from: any; to: any }> {
    const diff: Record<string, { from: any; to: any }> = {};

    for (const key in newState) {
      if (
        JSON.stringify(oldState[key as keyof GameState]) !==
        JSON.stringify(newState[key as keyof GameState])
      ) {
        diff[key] = {
          from: oldState[key as keyof GameState],
          to: newState[key as keyof GameState],
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
    this.dispatchEvent(
      new CustomEvent('stateChange', {
        detail: { state: frozenState },
      })
    );
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
    return hand.every((piece) => (piece.value || 0) <= 9);
  }

  /**
   * Calculate total hand value
   */
  private calculateHandValue(hand: any[]): number {
    if (!hand || hand.length === 0) return 0;
    return hand.reduce((sum, piece) => sum + (piece.value || 0), 0);
  }

  /**
   * Calculate highest card value in hand
   */
  private calculateHighestCardValue(hand: any[]): number {
    if (!hand || hand.length === 0) return 0;
    return Math.max(...hand.map((piece) => piece.value || 0));
  }

  /**
   * Calculate estimated piles from hand strength
   */
  private calculateEstimatedPiles(hand: any[]): number {
    if (!hand || hand.length === 0) return 0;

    const values = hand.map((piece) => piece.value || 0);
    const averageValue =
      values.reduce((sum, val) => sum + val, 0) / values.length;
    const highCards = values.filter((val) => val > 10).length;

    // Rough estimation: more high cards = more potential piles
    return Math.max(0, Math.min(8, Math.floor(averageValue / 4) + highCards));
  }

  /**
   * Calculate hand strength score
   */
  private calculateHandStrength(hand: any[]): number {
    if (!hand || hand.length === 0) return 0;

    const values = hand.map((piece) => piece.value || 0);
    const averageValue =
      values.reduce((sum, val) => sum + val, 0) / values.length;
    const maxValue = Math.max(...values);

    // Normalize to 0-100 scale
    return Math.min(100, Math.round(averageValue * 2 + maxValue / 2));
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
    return players
      .map((player) => {
        // Handle backend scoring objects vs simple numbers
        const playerRoundScore = roundScores[player.name];
        const roundScore =
          typeof playerRoundScore === 'object' &&
          playerRoundScore?.final_score !== undefined
            ? playerRoundScore.final_score
            : playerRoundScore || 0;

        const baseScore =
          typeof playerRoundScore === 'object' &&
          playerRoundScore?.base_score !== undefined
            ? playerRoundScore.base_score
            : Math.round(roundScore / Math.max(1, redealMultiplier));

        const actualPiles =
          typeof playerRoundScore === 'object' &&
          playerRoundScore?.actual !== undefined
            ? playerRoundScore.actual
            : this.deriveActualPiles(player, roundScore);

        const declaredPiles =
          typeof playerRoundScore === 'object' &&
          playerRoundScore?.declared !== undefined
            ? playerRoundScore.declared
            : player.pile_count || 0;

        const totalScore =
          typeof playerRoundScore === 'object' &&
          playerRoundScore?.total_score !== undefined
            ? playerRoundScore.total_score
            : totalScores[player.name] || 0;

        // Extract bonus and hit_value from backend
        const bonus =
          typeof playerRoundScore === 'object' &&
          playerRoundScore?.bonus !== undefined
            ? playerRoundScore.bonus
            : 0;

        const hitValue =
          typeof playerRoundScore === 'object' &&
          playerRoundScore?.hit_value !== undefined
            ? playerRoundScore.hit_value
            : actualPiles === declaredPiles
              ? declaredPiles
              : -Math.abs(declaredPiles - actualPiles);

        return {
          ...player,
          roundScore,
          totalScore,
          baseScore,
          actualPiles,
          pile_count: declaredPiles, // Add declared value for ScoringUI
          bonus, // Add bonus from backend
          hitValue, // Add hit value from backend
          scoreExplanation: this.generateScoreExplanation(
            player,
            roundScore,
            redealMultiplier
          ),
          isWinner: winners.includes(player.name),
        };
      })
      .sort((a, b) => b.totalScore - a.totalScore);
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
  private generateScoreExplanation(
    player: any,
    roundScore: number,
    redealMultiplier: number
  ): string {
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
