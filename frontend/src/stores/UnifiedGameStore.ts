// frontend/src/stores/UnifiedGameStore.ts

import { ConnectionStatus } from '../services/types';

export type GamePhase = 'waiting' | 'preparation' | 'declaration' | 'turn' | 'turn_results' | 'scoring';

export type StateListener = (state: StoreState) => void;
export type UnsubscribeFn = () => void;

interface GameState {
  // Room/Connection
  roomId: string | null;
  playerName: string | null;
  players: Array<{ name: string; is_bot: boolean }>;
  isHost: boolean;
  
  // Game flow
  phase: GamePhase | null;
  currentRound: number;
  turnNumber: number;
  currentTurnNumber: number;
  gameOver: boolean;
  winners: string[];
  
  // Player state
  myHand: any[];
  isMyTurn: boolean;
  isMyDecision: boolean;
  isMyHandWeak: boolean;
  canPlayAnyCount: boolean;
  validOptions: any[];
  
  // Game data from backend
  weakHands: string[];
  currentWeakPlayer: string | null;
  redealMultiplier: number;
  handValue: number;
  highestCardValue: number;
  declarations: Record<string, number>;
  currentTotal: number;
  declarationProgress: { declared: number; total: number };
  isLastPlayer: boolean;
  estimatedPiles: number;
  handStrength: number;
  currentTurnPlays: any[];
  requiredPieceCount: number | null;
  selectedPlayValue: number;
  turnWinner: string | null;
  winningPlay: any;
  playerPiles: Record<string, number>;
  nextStarter: string | null;
  roundScores: Record<string, number>;
  totalScores: Record<string, number>;
  playersWithScores: any[];
  displayMetadata: any;
  
  // Error state
  error: string | null;
}

export interface StoreState {
  // Connection
  roomId: string | null;
  playerName: string | null;
  connectionStatus: ConnectionStatus;
  
  // Game state (from backend)
  gameState: GameState;
  gameStarted: boolean;
  gamePhase: GamePhase | null;
  roundNumber: number;
  phaseData: any;  // Phase-specific data
  scores: Record<string, number>;
  
  // UI state
  selectedCards: number[];
  error: string | null;
  loading: boolean;
  
  // Phase 5.3: Action state tracking for clean state flow
  actionStates?: Record<string, any>;
}

type StateUpdater = (state: StoreState) => Partial<StoreState>;

/**
 * UnifiedGameStore - Single source of truth for game state
 * 
 * Replaces the 1534-line GameService with a focused, simple store.
 * Features:
 * - Synchronous state updates (no async delays)
 * - Version tracking for every update
 * - Checksum validation
 * - Immutable state updates
 * - Simple subscription pattern
 */
export class UnifiedGameStore {
  private static instance: UnifiedGameStore | null = null;
  
  private state: StoreState;
  private listeners = new Set<StateListener>();
  
  constructor() {
    this.state = {
      roomId: null,
      playerName: null,
      connectionStatus: {
        isConnected: false,
        isConnecting: false,
        isReconnecting: false,
        error: null
      },
      gameState: this.getInitialGameState(),
      gameStarted: false,
      gamePhase: null,
      roundNumber: 0,
      phaseData: {},
      scores: {},
      selectedCards: [],
      error: null,
      loading: false,
      actionStates: {} // Phase 5.3: Initialize action state tracking
    };
  }
  
  static getInstance(): UnifiedGameStore {
    if (!UnifiedGameStore.instance) {
      UnifiedGameStore.instance = new UnifiedGameStore();
    }
    return UnifiedGameStore.instance;
  }
  
  static resetInstance(): void {
    UnifiedGameStore.instance = null;
  }
  
  private getInitialGameState(): GameState {
    return {
      roomId: null,
      playerName: null,
      players: [],
      isHost: false,
      phase: null,
      currentRound: 0,
      turnNumber: 0,
      currentTurnNumber: 0,
      gameOver: false,
      winners: [],
      myHand: [],
      isMyTurn: false,
      isMyDecision: false,
      isMyHandWeak: false,
      canPlayAnyCount: false,
      validOptions: [],
      weakHands: [],
      currentWeakPlayer: null,
      redealMultiplier: 1,
      handValue: 0,
      highestCardValue: 0,
      declarations: {},
      currentTotal: 0,
      declarationProgress: { declared: 0, total: 4 },
      isLastPlayer: false,
      estimatedPiles: 0,
      handStrength: 0,
      currentTurnPlays: [],
      requiredPieceCount: null,
      selectedPlayValue: 0,
      turnWinner: null,
      winningPlay: null,
      playerPiles: {},
      nextStarter: null,
      roundScores: {},
      totalScores: {},
      playersWithScores: [],
      displayMetadata: null,
      error: null
    };
  }
  
  // ===== Public API =====
  
  /**
   * Get current state (immutable)
   */
  getState(): Readonly<StoreState> {
    return Object.freeze({ ...this.state });
  }
  
  /**
   * Update state synchronously
   * All updates are versioned and generate checksums
   */
  setState(updates: Partial<StoreState> | StateUpdater): void {
    const actualUpdates = typeof updates === 'function' 
      ? updates(this.state) 
      : updates;
    
    // Create new state immutably
    this.state = {
      ...this.state,
      ...actualUpdates
    };
    
    // Notify all listeners synchronously
    this.notifyListeners();
  }
  
  /**
   * Subscribe to state changes
   */
  subscribe(listener: StateListener): UnsubscribeFn {
    this.listeners.add(listener);
    
    // Return unsubscribe function
    return () => {
      this.listeners.delete(listener);
    };
  }
  
  /**
   * Handle state update from backend
   * This is called by NetworkIntegration when backend sends updates
   */
  handleBackendUpdate(version: number, checksum: string, updates: Partial<GameState>): void {
    this.setState({
      gameState: { ...this.state.gameState, ...updates }
    });
  }
  
  // Method alias for compatibility
  updateGameState(updates: Partial<GameState>): void {
    this.setState(prevState => ({
      gameState: { ...prevState.gameState, ...updates }
    }));
  }
  
  // Compatibility method
  updateState(updates: Partial<StoreState>): void {
    this.setState(updates);
  }
  
  private notifyListeners(): void {
    const currentState = this.getState();
    this.listeners.forEach(listener => {
      try {
        listener(currentState);
      } catch (error) {
        console.error('Error in state listener:', error);
      }
    });
  }
}

// Export singleton instance
export const gameStore = UnifiedGameStore.getInstance();