/**
 * 🔍 **StateDebugger Tool** - Phase 6.2 Live State Inspection
 * 
 * Real-time debugging tool for inspecting game state during active gameplay:
 * ✅ Live monitoring of frontend vs backend state differences
 * ✅ Real-time state synchronization tracking
 * ✅ Interactive state inspector with expandable object trees
 * ✅ WebSocket message viewer with filtering
 * ✅ State comparison with diff highlighting
 * ✅ Performance metrics and timing analysis
 */

import { networkService } from '../services/NetworkService';
import { gameStore } from '../stores/UnifiedGameStore';
import type { NetworkMessage, NetworkEventDetail } from '../services/types';

export interface StateSnapshot {
  id: string;
  timestamp: number;
  source: 'frontend' | 'backend';
  roomId: string;
  gameState: any;
  metadata: {
    phase?: string;
    playerName?: string;
    sequence?: number;
    checksum?: string;
  };
}

export interface StateDifference {
  path: string;
  frontendValue: any;
  backendValue: any;
  type: 'missing' | 'different' | 'extra';
  severity: 'low' | 'medium' | 'high' | 'critical';
}

export interface WebSocketMessage {
  id: string;
  timestamp: number;
  direction: 'incoming' | 'outgoing';
  event: string;
  data: any;
  roomId: string;
  metadata: {
    sequence?: number;
    size: number;
    latency?: number;
  };
}

export interface PerformanceMetrics {
  stateUpdateLatency: {
    average: number;
    min: number;
    max: number;
    recent: number[];
  };
  websocketLatency: {
    average: number;
    min: number;
    max: number;
    recent: number[];
  };
  renderLatency: {
    average: number;
    min: number;
    max: number;
    recent: number[];
  };
  eventProcessingTime: {
    average: number;
    min: number;
    max: number;
    recent: number[];
  };
}

export interface DebuggerState {
  isActive: boolean;
  roomId: string | null;
  playerName: string | null;
  
  // State tracking
  frontendState: any;
  backendState: any;
  lastStateUpdate: number;
  stateDifferences: StateDifference[];
  
  // Message tracking
  recentMessages: WebSocketMessage[];
  messageFilters: {
    showIncoming: boolean;
    showOutgoing: boolean;
    eventFilter: string;
    maxMessages: number;
  };
  
  // Performance tracking
  performanceMetrics: PerformanceMetrics;
  
  // View options
  viewOptions: {
    showStateComparison: boolean;
    showMessages: boolean;
    showPerformance: boolean;
    autoUpdate: boolean;
    updateInterval: number;
    maxHistorySize: number;
  };
}

export class StateDebugger extends EventTarget {
  private static instance: StateDebugger | null = null;
  
  static getInstance(): StateDebugger {
    if (!StateDebugger.instance) {
      StateDebugger.instance = new StateDebugger();
    }
    return StateDebugger.instance;
  }

  private state: DebuggerState = {
    isActive: false,
    roomId: null,
    playerName: null,
    frontendState: null,
    backendState: null,
    lastStateUpdate: 0,
    stateDifferences: [],
    recentMessages: [],
    messageFilters: {
      showIncoming: true,
      showOutgoing: true,
      eventFilter: '',
      maxMessages: 100
    },
    performanceMetrics: {
      stateUpdateLatency: { average: 0, min: 0, max: 0, recent: [] },
      websocketLatency: { average: 0, min: 0, max: 0, recent: [] },
      renderLatency: { average: 0, min: 0, max: 0, recent: [] },
      eventProcessingTime: { average: 0, min: 0, max: 0, recent: [] }
    },
    viewOptions: {
      showStateComparison: true,
      showMessages: true,
      showPerformance: true,
      autoUpdate: true,
      updateInterval: 1000,
      maxHistorySize: 1000
    }
  };

  private stateHistory: StateSnapshot[] = [];
  private performanceTimers = new Map<string, number>();
  private updateTimer: NodeJS.Timeout | null = null;
  private isDestroyed = false;

  private constructor() {
    super();
    this.setupEventListeners();
    console.log('🔍 StateDebugger: Initialized');
  }

  // ===== PUBLIC API =====

  /**
   * Start debugging for a specific room
   */
  startDebugging(roomId: string, playerName: string): void {
    if (this.isDestroyed) {
      throw new Error('StateDebugger has been destroyed');
    }

    this.state.isActive = true;
    this.state.roomId = roomId;
    this.state.playerName = playerName;
    this.state.lastStateUpdate = Date.now();

    // Capture initial state
    this.captureCurrentState();

    // Start auto-update if enabled
    if (this.state.viewOptions.autoUpdate) {
      this.startAutoUpdate();
    }

    this.dispatchEvent(new CustomEvent('debuggingStarted', {
      detail: { roomId, playerName }
    }));

    console.log(`🔍 State debugging started for room ${roomId}, player ${playerName}`);
  }

  /**
   * Stop debugging
   */
  stopDebugging(): void {
    if (!this.state.isActive) return;

    this.state.isActive = false;
    this.stopAutoUpdate();

    this.dispatchEvent(new CustomEvent('debuggingStopped', {
      detail: { roomId: this.state.roomId }
    }));

    console.log('🔍 State debugging stopped');
  }

  /**
   * Manually capture current state snapshot
   */
  captureCurrentState(): void {
    if (!this.state.isActive) return;

    const timestamp = Date.now();
    const frontendState = gameStore.getState().gameState;

    // Create frontend snapshot
    const frontendSnapshot: StateSnapshot = {
      id: crypto.randomUUID(),
      timestamp,
      source: 'frontend',
      roomId: this.state.roomId!,
      gameState: JSON.parse(JSON.stringify(frontendState)),
      metadata: {
        phase: frontendState?.phase || undefined,
        playerName: this.state.playerName!,
        checksum: this.calculateChecksum(frontendState)
      }
    };

    this.stateHistory.push(frontendSnapshot);
    this.state.frontendState = frontendSnapshot.gameState;

    // Limit history size
    if (this.stateHistory.length > this.state.viewOptions.maxHistorySize) {
      this.stateHistory.shift();
    }

    // Compare states and find differences
    if (this.state.backendState) {
      this.compareStates();
    }

    this.dispatchEvent(new CustomEvent('stateUpdated', {
      detail: { snapshot: frontendSnapshot }
    }));
  }

  /**
   * Get current debugger state
   */
  getState(): DebuggerState {
    return { ...this.state };
  }

  /**
   * Get recent state snapshots
   */
  getStateHistory(limit?: number): StateSnapshot[] {
    const snapshots = this.stateHistory;
    return limit ? snapshots.slice(-limit) : snapshots;
  }

  /**
   * Get filtered WebSocket messages
   */
  getFilteredMessages(): WebSocketMessage[] {
    const filters = this.state.messageFilters;
    
    return this.state.recentMessages.filter(msg => {
      // Direction filter
      if (!filters.showIncoming && msg.direction === 'incoming') return false;
      if (!filters.showOutgoing && msg.direction === 'outgoing') return false;
      
      // Event filter
      if (filters.eventFilter && !msg.event.toLowerCase().includes(filters.eventFilter.toLowerCase())) {
        return false;
      }
      
      return true;
    }).slice(-filters.maxMessages);
  }

  /**
   * Update message filters
   */
  setMessageFilters(filters: Partial<DebuggerState['messageFilters']>): void {
    this.state.messageFilters = {
      ...this.state.messageFilters,
      ...filters
    };

    this.dispatchEvent(new CustomEvent('filtersChanged', {
      detail: { filters: this.state.messageFilters }
    }));
  }

  /**
   * Update view options
   */
  setViewOptions(options: Partial<DebuggerState['viewOptions']>): void {
    const oldOptions = this.state.viewOptions;
    this.state.viewOptions = {
      ...this.state.viewOptions,
      ...options
    };

    // Handle auto-update changes
    if (oldOptions.autoUpdate !== this.state.viewOptions.autoUpdate) {
      if (this.state.viewOptions.autoUpdate && this.state.isActive) {
        this.startAutoUpdate();
      } else {
        this.stopAutoUpdate();
      }
    }

    // Handle interval changes
    if (oldOptions.updateInterval !== this.state.viewOptions.updateInterval) {
      if (this.state.viewOptions.autoUpdate && this.state.isActive) {
        this.stopAutoUpdate();
        this.startAutoUpdate();
      }
    }

    this.dispatchEvent(new CustomEvent('viewOptionsChanged', {
      detail: { options: this.state.viewOptions }
    }));
  }

  /**
   * Clear all debugging data
   */
  clearData(): void {
    this.stateHistory = [];
    this.state.recentMessages = [];
    this.state.stateDifferences = [];
    this.performanceTimers.clear();
    
    // Reset performance metrics
    this.state.performanceMetrics = {
      stateUpdateLatency: { average: 0, min: 0, max: 0, recent: [] },
      websocketLatency: { average: 0, min: 0, max: 0, recent: [] },
      renderLatency: { average: 0, min: 0, max: 0, recent: [] },
      eventProcessingTime: { average: 0, min: 0, max: 0, recent: [] }
    };

    this.dispatchEvent(new CustomEvent('dataCleared', {
      detail: { timestamp: Date.now() }
    }));

    console.log('🔍 Debugging data cleared');
  }

  /**
   * Export debugging session data
   */
  exportData(): string {
    const exportData = {
      sessionInfo: {
        roomId: this.state.roomId,
        playerName: this.state.playerName,
        startTime: this.stateHistory[0]?.timestamp,
        endTime: this.stateHistory[this.stateHistory.length - 1]?.timestamp,
        duration: Date.now() - (this.stateHistory[0]?.timestamp || Date.now())
      },
      stateHistory: this.stateHistory,
      messages: this.state.recentMessages,
      differences: this.state.stateDifferences,
      performanceMetrics: this.state.performanceMetrics,
      version: '1.0.0'
    };

    return JSON.stringify(exportData, null, 2);
  }

  /**
   * Destroy the debugger
   */
  destroy(): void {
    this.isDestroyed = true;
    this.stopDebugging();
    this.clearData();
    
    StateDebugger.instance = null;
    console.log('🔍 StateDebugger: Destroyed');
  }

  // ===== PRIVATE METHODS =====

  /**
   * Setup event listeners
   */
  private setupEventListeners(): void {
    // Listen to network events
    networkService.addEventListener('message', this.handleIncomingMessage.bind(this));
    
    // Listen to state changes
    gameStore.subscribe(this.handleStateChange.bind(this));

    // Intercept outgoing messages
    this.interceptNetworkSend();
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleIncomingMessage(event: Event): void {
    if (!this.state.isActive) return;

    const customEvent = event as CustomEvent<NetworkEventDetail>;
    const { roomId, message, data } = customEvent.detail;

    if (roomId !== this.state.roomId) return;

    const wsMessage: WebSocketMessage = {
      id: crypto.randomUUID(),
      timestamp: Date.now(),
      direction: 'incoming',
      event: message?.event || 'unknown',
      data: data || message?.data,
      roomId,
      metadata: {
        sequence: message?.sequence,
        size: JSON.stringify(data || message?.data || {}).length
      }
    };

    this.addMessage(wsMessage);

    // Track backend state updates
    if (message?.event === 'phase_change' || data?.phase) {
      this.handleBackendStateUpdate(data || message?.data);
    }

    // Measure processing time
    this.measureEventProcessingTime();
  }

  /**
   * Handle outgoing WebSocket messages
   */
  private handleOutgoingMessage(roomId: string, event: string, data: any): void {
    if (!this.state.isActive || roomId !== this.state.roomId) return;

    const wsMessage: WebSocketMessage = {
      id: crypto.randomUUID(),
      timestamp: Date.now(),
      direction: 'outgoing',
      event,
      data,
      roomId,
      metadata: {
        size: JSON.stringify(data).length
      }
    };

    this.addMessage(wsMessage);
  }

  /**
   * Handle frontend state changes
   */
  private handleStateChange(newState: any): void {
    if (!this.state.isActive) return;

    const now = Date.now();
    const latency = now - this.state.lastStateUpdate;
    
    // Update performance metrics
    this.updatePerformanceMetric('stateUpdateLatency', latency);
    
    this.state.lastStateUpdate = now;
    this.captureCurrentState();
  }

  /**
   * Handle backend state updates
   */
  private handleBackendStateUpdate(data: any): void {
    if (!data) return;

    const backendSnapshot: StateSnapshot = {
      id: crypto.randomUUID(),
      timestamp: Date.now(),
      source: 'backend',
      roomId: this.state.roomId!,
      gameState: JSON.parse(JSON.stringify(data)),
      metadata: {
        phase: data.phase,
        playerName: this.state.playerName!,
        sequence: data.sequence,
        checksum: this.calculateChecksum(data)
      }
    };

    this.stateHistory.push(backendSnapshot);
    this.state.backendState = backendSnapshot.gameState;

    // Compare with frontend state
    this.compareStates();

    this.dispatchEvent(new CustomEvent('backendStateUpdated', {
      detail: { snapshot: backendSnapshot }
    }));
  }

  /**
   * Compare frontend and backend states
   */
  private compareStates(): void {
    if (!this.state.frontendState || !this.state.backendState) return;

    const differences = this.findStateDifferences(
      this.state.frontendState,
      this.state.backendState,
      ''
    );

    this.state.stateDifferences = differences;

    if (differences.length > 0) {
      this.dispatchEvent(new CustomEvent('stateDifferencesFound', {
        detail: { differences, count: differences.length }
      }));
    }
  }

  /**
   * Find differences between two state objects
   */
  private findStateDifferences(
    frontendObj: any,
    backendObj: any,
    path: string
  ): StateDifference[] {
    const differences: StateDifference[] = [];

    // Handle null/undefined cases
    if (frontendObj === null || frontendObj === undefined) {
      if (backendObj !== null && backendObj !== undefined) {
        differences.push({
          path,
          frontendValue: frontendObj,
          backendValue: backendObj,
          type: 'missing',
          severity: this.getSeverity(path)
        });
      }
      return differences;
    }

    if (backendObj === null || backendObj === undefined) {
      differences.push({
        path,
        frontendValue: frontendObj,
        backendValue: backendObj,
        type: 'extra',
        severity: this.getSeverity(path)
      });
      return differences;
    }

    // Handle primitive types
    if (typeof frontendObj !== 'object' || typeof backendObj !== 'object') {
      if (frontendObj !== backendObj) {
        differences.push({
          path,
          frontendValue: frontendObj,
          backendValue: backendObj,
          type: 'different',
          severity: this.getSeverity(path)
        });
      }
      return differences;
    }

    // Handle arrays
    if (Array.isArray(frontendObj) && Array.isArray(backendObj)) {
      const maxLength = Math.max(frontendObj.length, backendObj.length);
      for (let i = 0; i < maxLength; i++) {
        const newPath = `${path}[${i}]`;
        differences.push(...this.findStateDifferences(
          frontendObj[i],
          backendObj[i],
          newPath
        ));
      }
      return differences;
    }

    // Handle objects
    const allKeys = new Set([
      ...Object.keys(frontendObj || {}),
      ...Object.keys(backendObj || {})
    ]);

    for (const key of allKeys) {
      const newPath = path ? `${path}.${key}` : key;
      differences.push(...this.findStateDifferences(
        frontendObj[key],
        backendObj[key],
        newPath
      ));
    }

    return differences;
  }

  /**
   * Get severity level for a state difference
   */
  private getSeverity(path: string): StateDifference['severity'] {
    // Critical differences that affect gameplay
    if (path.includes('phase') || path.includes('currentPlayer') || path.includes('gameOver')) {
      return 'critical';
    }
    
    // High severity for player state
    if (path.includes('players') || path.includes('myHand') || path.includes('scores')) {
      return 'high';
    }
    
    // Medium severity for game state
    if (path.includes('round') || path.includes('turn') || path.includes('declarations')) {
      return 'medium';
    }
    
    // Low severity for UI state
    return 'low';
  }

  /**
   * Add message to recent messages list
   */
  private addMessage(message: WebSocketMessage): void {
    this.state.recentMessages.push(message);
    
    // Limit message history
    if (this.state.recentMessages.length > this.state.messageFilters.maxMessages * 2) {
      this.state.recentMessages = this.state.recentMessages.slice(-this.state.messageFilters.maxMessages);
    }
  }

  /**
   * Intercept network send method
   */
  private interceptNetworkSend(): void {
    const originalSend = networkService.send.bind(networkService);
    
    networkService.send = (roomId: string, event: string, data: Record<string, any> = {}) => {
      this.handleOutgoingMessage(roomId, event, data);
      return originalSend(roomId, event, data);
    };
  }

  /**
   * Update performance metric
   */
  private updatePerformanceMetric(metric: keyof PerformanceMetrics, value: number): void {
    const metricData = this.state.performanceMetrics[metric];
    
    metricData.recent.push(value);
    if (metricData.recent.length > 100) {
      metricData.recent.shift();
    }
    
    metricData.min = metricData.min === 0 ? value : Math.min(metricData.min, value);
    metricData.max = Math.max(metricData.max, value);
    metricData.average = metricData.recent.reduce((a, b) => a + b, 0) / metricData.recent.length;
  }

  /**
   * Measure event processing time
   */
  private measureEventProcessingTime(): void {
    const now = performance.now();
    const timerId = 'event_processing';
    
    if (this.performanceTimers.has(timerId)) {
      const startTime = this.performanceTimers.get(timerId)!;
      const duration = now - startTime;
      this.updatePerformanceMetric('eventProcessingTime', duration);
    }
    
    this.performanceTimers.set(timerId, now);
  }

  /**
   * Calculate checksum for state object
   */
  private calculateChecksum(obj: any): string {
    const str = JSON.stringify(obj, Object.keys(obj).sort());
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash).toString(36);
  }

  /**
   * Start auto-update timer
   */
  private startAutoUpdate(): void {
    this.stopAutoUpdate();
    
    this.updateTimer = setInterval(() => {
      if (this.state.isActive) {
        this.captureCurrentState();
      }
    }, this.state.viewOptions.updateInterval);
  }

  /**
   * Stop auto-update timer
   */
  private stopAutoUpdate(): void {
    if (this.updateTimer) {
      clearInterval(this.updateTimer);
      this.updateTimer = null;
    }
  }
}

// Export singleton instance
export const stateDebugger = StateDebugger.getInstance();