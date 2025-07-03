/**
 * 🎮 **GameReplay Tool** - Phase 6.1 Game Replay for Debugging
 * 
 * Records and replays game sessions for debugging player-reported issues:
 * ✅ Records all game events (actions, state changes, WebSocket messages)
 * ✅ Step-by-step replay with pause/rewind/fast-forward controls
 * ✅ Visual timeline with event filtering
 * ✅ Export/import replay files for team sharing
 * ✅ Integration with existing event system
 */

import { networkService } from '../services/NetworkService';
import { gameStore } from '../stores/UnifiedGameStore';
import type { NetworkMessage, NetworkEventDetail } from '../services/types';

export interface ReplayEvent {
  id: string;
  timestamp: number;
  sequence: number;
  type: 'network_message' | 'state_change' | 'user_action' | 'system_event';
  source: 'frontend' | 'backend' | 'user';
  roomId: string;
  data: any;
  metadata?: {
    playerName?: string;
    phase?: string;
    actionType?: string;
    success?: boolean;
    error?: string;
  };
}

export interface ReplaySession {
  id: string;
  roomId: string;
  playerName: string;
  startTime: number;
  endTime?: number;
  events: ReplayEvent[];
  gameMetadata: {
    totalPlayers: number;
    gamePhases: string[];
    totalRounds: number;
    finalScores?: Record<string, number>;
  };
  version: string;
}

export interface ReplayState {
  isRecording: boolean;
  isReplaying: boolean;
  currentSession: ReplaySession | null;
  currentEventIndex: number;
  playbackSpeed: number; // 0.25x to 4x
  isPaused: boolean;
  eventFilters: {
    showNetworkMessages: boolean;
    showStateChanges: boolean;
    showUserActions: boolean;
    showSystemEvents: boolean;
    playerFilter?: string;
    phaseFilter?: string;
  };
}

export class GameReplayManager extends EventTarget {
  private static instance: GameReplayManager | null = null;
  
  static getInstance(): GameReplayManager {
    if (!GameReplayManager.instance) {
      GameReplayManager.instance = new GameReplayManager();
    }
    return GameReplayManager.instance;
  }

  private state: ReplayState = {
    isRecording: false,
    isReplaying: false,
    currentSession: null,
    currentEventIndex: 0,
    playbackSpeed: 1.0,
    isPaused: false,
    eventFilters: {
      showNetworkMessages: true,
      showStateChanges: true,
      showUserActions: true,
      showSystemEvents: true
    }
  };

  private eventSequence = 0;
  private replayTimer: NodeJS.Timeout | null = null;
  private originalNetworkSend!: typeof networkService.send;
  private isDestroyed = false;

  private constructor() {
    super();
    this.setupEventListeners();
    console.log('🎮 GameReplayManager: Initialized');
  }

  // ===== PUBLIC API =====

  /**
   * Start recording a new replay session
   */
  startRecording(roomId: string, playerName: string): ReplaySession {
    if (this.isDestroyed) {
      throw new Error('GameReplayManager has been destroyed');
    }

    if (this.state.isRecording) {
      this.stopRecording();
    }

    const session: ReplaySession = {
      id: crypto.randomUUID(),
      roomId,
      playerName,
      startTime: Date.now(),
      events: [],
      gameMetadata: {
        totalPlayers: 0,
        gamePhases: [],
        totalRounds: 0
      },
      version: '1.0.0'
    };

    this.state.currentSession = session;
    this.state.isRecording = true;
    this.eventSequence = 0;

    // Record initial state
    this.recordEvent({
      type: 'system_event',
      source: 'frontend',
      data: {
        type: 'recording_started',
        initialGameState: gameStore.getState().gameState
      },
      metadata: {
        playerName
      }
    });

    this.dispatchEvent(new CustomEvent('recordingStarted', {
      detail: { session }
    }));

    console.log(`🎮 Recording started for room ${roomId}, player ${playerName}`);
    return session;
  }

  /**
   * Stop recording current session
   */
  stopRecording(): ReplaySession | null {
    if (!this.state.isRecording || !this.state.currentSession) {
      return null;
    }

    this.state.currentSession.endTime = Date.now();
    
    // Record final state
    this.recordEvent({
      type: 'system_event',
      source: 'frontend',
      data: {
        type: 'recording_stopped',
        finalGameState: gameStore.getState().gameState
      }
    });

    // Update game metadata
    this.updateGameMetadata();

    const session = this.state.currentSession;
    this.state.isRecording = false;

    this.dispatchEvent(new CustomEvent('recordingStopped', {
      detail: { session }
    }));

    console.log(`🎮 Recording stopped. Captured ${session.events.length} events over ${(session.endTime || Date.now()) - session.startTime}ms`);
    return session;
  }

  /**
   * Start replaying a session
   */
  startReplay(session: ReplaySession): void {
    if (this.state.isRecording) {
      throw new Error('Cannot replay while recording');
    }

    this.state.currentSession = session;
    this.state.isReplaying = true;
    this.state.currentEventIndex = 0;
    this.state.isPaused = false;

    // Reset game state to initial state if available
    const initialEvent = session.events.find(e => e.data?.type === 'recording_started');
    if (initialEvent?.data?.initialGameState) {
      gameStore.setState({
        gameState: initialEvent.data.initialGameState
      });
    }

    this.dispatchEvent(new CustomEvent('replayStarted', {
      detail: { session }
    }));

    console.log(`🎮 Replay started for session ${session.id}`);
    this.scheduleNextEvent();
  }

  /**
   * Stop current replay
   */
  stopReplay(): void {
    if (!this.state.isReplaying) return;

    this.state.isReplaying = false;
    this.state.isPaused = false;
    
    if (this.replayTimer) {
      clearTimeout(this.replayTimer);
      this.replayTimer = null;
    }

    this.dispatchEvent(new CustomEvent('replayStopped', {
      detail: { session: this.state.currentSession }
    }));

    console.log('🎮 Replay stopped');
  }

  /**
   * Pause/resume replay
   */
  togglePause(): void {
    if (!this.state.isReplaying) return;

    this.state.isPaused = !this.state.isPaused;

    if (this.state.isPaused) {
      if (this.replayTimer) {
        clearTimeout(this.replayTimer);
        this.replayTimer = null;
      }
    } else {
      this.scheduleNextEvent();
    }

    this.dispatchEvent(new CustomEvent('replayPauseToggled', {
      detail: { isPaused: this.state.isPaused }
    }));

    console.log(`🎮 Replay ${this.state.isPaused ? 'paused' : 'resumed'}`);
  }

  /**
   * Jump to specific event index
   */
  jumpToEvent(eventIndex: number): void {
    if (!this.state.currentSession) return;

    const session = this.state.currentSession;
    const targetIndex = Math.max(0, Math.min(eventIndex, session.events.length - 1));
    
    this.state.currentEventIndex = targetIndex;

    // Apply all events up to target index
    this.replayToIndex(targetIndex);

    this.dispatchEvent(new CustomEvent('replayJumped', {
      detail: { eventIndex: targetIndex }
    }));

    console.log(`🎮 Jumped to event ${targetIndex}`);
  }

  /**
   * Step forward one event
   */
  stepForward(): void {
    if (!this.state.currentSession) return;

    const nextIndex = this.state.currentEventIndex + 1;
    if (nextIndex < this.state.currentSession.events.length) {
      this.jumpToEvent(nextIndex);
    }
  }

  /**
   * Step backward one event
   */
  stepBackward(): void {
    if (!this.state.currentSession) return;

    const prevIndex = this.state.currentEventIndex - 1;
    if (prevIndex >= 0) {
      this.jumpToEvent(prevIndex);
    }
  }

  /**
   * Set playback speed
   */
  setPlaybackSpeed(speed: number): void {
    this.state.playbackSpeed = Math.max(0.25, Math.min(4.0, speed));
    
    this.dispatchEvent(new CustomEvent('playbackSpeedChanged', {
      detail: { speed: this.state.playbackSpeed }
    }));
  }

  /**
   * Update event filters
   */
  setEventFilters(filters: Partial<ReplayState['eventFilters']>): void {
    this.state.eventFilters = {
      ...this.state.eventFilters,
      ...filters
    };

    this.dispatchEvent(new CustomEvent('filtersChanged', {
      detail: { filters: this.state.eventFilters }
    }));
  }

  /**
   * Export replay session to JSON
   */
  exportSession(session: ReplaySession): string {
    return JSON.stringify(session, null, 2);
  }

  /**
   * Import replay session from JSON
   */
  importSession(jsonData: string): ReplaySession {
    try {
      const session = JSON.parse(jsonData) as ReplaySession;
      
      // Validate session structure
      if (!session.id || !session.events || !Array.isArray(session.events)) {
        throw new Error('Invalid replay session format');
      }

      return session;
    } catch (error) {
      throw new Error(`Failed to import replay session: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Get current replay state
   */
  getState(): ReplayState {
    return { ...this.state };
  }

  /**
   * Get filtered events for display
   */
  getFilteredEvents(): ReplayEvent[] {
    if (!this.state.currentSession) return [];

    return this.state.currentSession.events.filter(event => {
      const filters = this.state.eventFilters;
      
      // Type filters
      if (!filters.showNetworkMessages && event.type === 'network_message') return false;
      if (!filters.showStateChanges && event.type === 'state_change') return false;
      if (!filters.showUserActions && event.type === 'user_action') return false;
      if (!filters.showSystemEvents && event.type === 'system_event') return false;
      
      // Player filter
      if (filters.playerFilter && event.metadata?.playerName !== filters.playerFilter) {
        return false;
      }
      
      // Phase filter
      if (filters.phaseFilter && event.metadata?.phase !== filters.phaseFilter) {
        return false;
      }

      return true;
    });
  }

  /**
   * Destroy the replay manager
   */
  destroy(): void {
    this.isDestroyed = true;
    this.stopRecording();
    this.stopReplay();
    
    // Restore original network send function
    if (this.originalNetworkSend) {
      networkService.send = this.originalNetworkSend;
    }

    GameReplayManager.instance = null;
    console.log('🎮 GameReplayManager: Destroyed');
  }

  // ===== PRIVATE METHODS =====

  /**
   * Setup event listeners for recording
   */
  private setupEventListeners(): void {
    // Listen to network events
    networkService.addEventListener('message', this.handleNetworkMessage.bind(this));
    networkService.addEventListener('connected', this.handleNetworkEvent.bind(this));
    networkService.addEventListener('disconnected', this.handleNetworkEvent.bind(this));
    networkService.addEventListener('reconnected', this.handleNetworkEvent.bind(this));

    // Listen to state changes
    gameStore.subscribe(this.handleStateChange.bind(this));

    // Intercept outgoing network messages
    this.originalNetworkSend = networkService.send.bind(networkService);
    networkService.send = this.interceptNetworkSend.bind(this);
  }

  /**
   * Record an event during recording
   */
  private recordEvent(eventData: Partial<ReplayEvent>): void {
    if (!this.state.isRecording || !this.state.currentSession) return;

    const event: ReplayEvent = {
      id: crypto.randomUUID(),
      timestamp: Date.now(),
      sequence: this.eventSequence++,
      roomId: this.state.currentSession.roomId,
      ...eventData
    } as ReplayEvent;

    this.state.currentSession.events.push(event);

    this.dispatchEvent(new CustomEvent('eventRecorded', {
      detail: { event }
    }));
  }

  /**
   * Handle incoming network messages
   */
  private handleNetworkMessage(event: Event): void {
    const customEvent = event as CustomEvent<NetworkEventDetail>;
    const { roomId, message, data } = customEvent.detail;

    this.recordEvent({
      type: 'network_message',
      source: 'backend',
      data: {
        event: message?.event || 'unknown',
        data: data || message?.data,
        message: message
      },
      metadata: {
        phase: data?.phase || message?.data?.phase
      }
    });
  }

  /**
   * Handle network connection events
   */
  private handleNetworkEvent(event: Event): void {
    const customEvent = event as CustomEvent;
    const { roomId } = customEvent.detail || {};

    this.recordEvent({
      type: 'system_event',
      source: 'frontend',
      data: {
        type: event.type,
        detail: customEvent.detail
      }
    });
  }

  /**
   * Handle state changes
   */
  private handleStateChange(newState: any): void {
    this.recordEvent({
      type: 'state_change',
      source: 'frontend',
      data: {
        gameState: newState.gameState,
        timestamp: Date.now()
      },
      metadata: {
        phase: newState.gameState?.phase
      }
    });
  }

  /**
   * Intercept outgoing network messages
   */
  private interceptNetworkSend(roomId: string, event: string, data: Record<string, any> = {}): boolean {
    // Record the user action
    this.recordEvent({
      type: 'user_action',
      source: 'user',
      data: {
        event,
        data,
        roomId
      },
      metadata: {
        playerName: this.state.currentSession?.playerName,
        actionType: event
      }
    });

    // Call original send function
    return this.originalNetworkSend(roomId, event, data);
  }

  /**
   * Schedule next event during replay
   */
  private scheduleNextEvent(): void {
    if (!this.state.isReplaying || this.state.isPaused || !this.state.currentSession) {
      return;
    }

    const session = this.state.currentSession;
    const currentIndex = this.state.currentEventIndex;

    if (currentIndex >= session.events.length) {
      this.stopReplay();
      return;
    }

    const currentEvent = session.events[currentIndex];
    const nextIndex = currentIndex + 1;

    if (nextIndex < session.events.length) {
      const nextEvent = session.events[nextIndex];
      const delay = (nextEvent.timestamp - currentEvent.timestamp) / this.state.playbackSpeed;

      this.replayTimer = setTimeout(() => {
        this.state.currentEventIndex = nextIndex;
        this.applyEvent(nextEvent);
        this.scheduleNextEvent();
      }, Math.max(10, delay)); // Minimum 10ms delay
    } else {
      // Replay finished
      this.stopReplay();
    }
  }

  /**
   * Apply a single event during replay
   */
  private applyEvent(event: ReplayEvent): void {
    switch (event.type) {
      case 'state_change':
        if (event.data?.gameState) {
          gameStore.setState({
            gameState: event.data.gameState
          });
        }
        break;

      case 'network_message':
        // Simulate receiving the network message
        this.dispatchEvent(new CustomEvent('replayNetworkMessage', {
          detail: { event, data: event.data }
        }));
        break;

      case 'user_action':
        this.dispatchEvent(new CustomEvent('replayUserAction', {
          detail: { event, action: event.data }
        }));
        break;

      case 'system_event':
        this.dispatchEvent(new CustomEvent('replaySystemEvent', {
          detail: { event, data: event.data }
        }));
        break;
    }

    this.dispatchEvent(new CustomEvent('eventApplied', {
      detail: { event, eventIndex: this.state.currentEventIndex }
    }));
  }

  /**
   * Replay all events up to specific index
   */
  private replayToIndex(targetIndex: number): void {
    if (!this.state.currentSession) return;

    const session = this.state.currentSession;
    
    // Find initial state
    const initialEvent = session.events.find(e => e.data?.type === 'recording_started');
    if (initialEvent?.data?.initialGameState) {
      gameStore.setState({
        gameState: initialEvent.data.initialGameState
      });
    }

    // Apply events up to target index
    for (let i = 0; i <= targetIndex && i < session.events.length; i++) {
      const event = session.events[i];
      if (event.type === 'state_change' && event.data?.gameState) {
        gameStore.setState({
          gameState: event.data.gameState
        });
      }
    }
  }

  /**
   * Update game metadata from recorded events
   */
  private updateGameMetadata(): void {
    if (!this.state.currentSession) return;

    const session = this.state.currentSession;
    const events = session.events;

    // Extract unique phases
    const phases = new Set<string>();
    let totalRounds = 0;
    let playerCount = 0;
    const finalScores: Record<string, number> = {};

    events.forEach(event => {
      if (event.metadata?.phase) {
        phases.add(event.metadata.phase);
      }

      if (event.type === 'state_change' && event.data?.gameState) {
        const gameState = event.data.gameState;
        
        if (gameState.currentRound > totalRounds) {
          totalRounds = gameState.currentRound;
        }
        
        if (gameState.players && gameState.players.length > playerCount) {
          playerCount = gameState.players.length;
        }

        if (gameState.totalScores) {
          Object.assign(finalScores, gameState.totalScores);
        }
      }
    });

    session.gameMetadata = {
      totalPlayers: playerCount,
      gamePhases: Array.from(phases),
      totalRounds,
      finalScores: Object.keys(finalScores).length > 0 ? finalScores : undefined
    };
  }
}

// Export singleton instance
export const gameReplayManager = GameReplayManager.getInstance();

// Export types for use in components (avoid conflicts)