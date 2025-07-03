/**
 * 🔄 **SyncChecker Tool** - Phase 6.3 Desync Detection
 * 
 * Specialized tool for detecting synchronization issues between frontend and backend:
 * ✅ Continuous monitoring of critical game state fields
 * ✅ Automatic desync alerts with severity levels
 * ✅ Historical desync tracking with timestamps
 * ✅ Recovery suggestions and automated fixes
 * ✅ Integration with existing debugging tools
 */

import { networkService } from '../services/NetworkService';
import { gameStore } from '../stores/UnifiedGameStore';
import type { NetworkMessage, NetworkEventDetail } from '../services/types';

export interface SyncPoint {
  id: string;
  timestamp: number;
  fieldPath: string;
  frontendValue: any;
  backendValue: any;
  isSync: boolean;
  severity: 'info' | 'warning' | 'error' | 'critical';
  context: {
    phase: string;
    playerName: string;
    sequence?: number;
    roomId: string;
  };
}

export interface DesyncEvent {
  id: string;
  timestamp: number;
  startTime: number;
  endTime?: number;
  affectedFields: string[];
  severity: 'low' | 'medium' | 'high' | 'critical';
  impact: {
    gameplayBlocking: boolean;
    userExperienceImpact: 'none' | 'minor' | 'major' | 'severe';
    dataIntegrity: 'safe' | 'risk' | 'corrupted';
  };
  resolution?: {
    method: 'auto_recovered' | 'manual_fix' | 'reconnect_required' | 'unsolved';
    timestamp: number;
    description: string;
  };
}

export interface SyncCheckerState {
  isActive: boolean;
  roomId: string | null;
  playerName: string | null;
  
  // Monitoring config
  checkInterval: number;
  criticalFields: string[];
  toleranceMs: number;
  
  // Current state
  lastSyncCheck: number;
  currentDesyncs: DesyncEvent[];
  syncHistory: SyncPoint[];
  
  // Statistics
  totalChecks: number;
  totalDesyncs: number;
  averageResolutionTime: number;
  
  // Alert settings
  alertSettings: {
    enableAudioAlerts: boolean;
    enableVisualAlerts: boolean;
    enableAutoRecovery: boolean;
    criticalOnly: boolean;
  };
}

export class SyncChecker extends EventTarget {
  private static instance: SyncChecker | null = null;
  
  static getInstance(): SyncChecker {
    if (!SyncChecker.instance) {
      SyncChecker.instance = new SyncChecker();
    }
    return SyncChecker.instance;
  }

  private state: SyncCheckerState = {
    isActive: false,
    roomId: null,
    playerName: null,
    checkInterval: 2000, // Check every 2 seconds
    criticalFields: [
      'phase',
      'currentPlayer',
      'currentRound',
      'turnNumber',
      'gameOver',
      'players',
      'myHand',
      'declarations',
      'scores',
      'totalScores'
    ],
    toleranceMs: 100, // 100ms tolerance for timing differences
    lastSyncCheck: 0,
    currentDesyncs: [],
    syncHistory: [],
    totalChecks: 0,
    totalDesyncs: 0,
    averageResolutionTime: 0,
    alertSettings: {
      enableAudioAlerts: true,
      enableVisualAlerts: true,
      enableAutoRecovery: true,
      criticalOnly: false
    }
  };

  private checkTimer: NodeJS.Timeout | null = null;
  private lastBackendState: any = null;
  private isDestroyed = false;

  private constructor() {
    super();
    this.setupEventListeners();
    console.log('🔄 SyncChecker: Initialized');
  }

  // ===== PUBLIC API =====

  /**
   * Start sync checking for a specific room
   */
  startChecking(roomId: string, playerName: string): void {
    if (this.isDestroyed) {
      throw new Error('SyncChecker has been destroyed');
    }

    this.state.isActive = true;
    this.state.roomId = roomId;
    this.state.playerName = playerName;
    this.state.lastSyncCheck = Date.now();

    // Start periodic checking
    this.startPeriodicChecking();

    this.dispatchEvent(new CustomEvent('checkingStarted', {
      detail: { roomId, playerName }
    }));

    console.log(`🔄 Sync checking started for room ${roomId}, player ${playerName}`);
  }

  /**
   * Stop sync checking
   */
  stopChecking(): void {
    if (!this.state.isActive) return;

    this.state.isActive = false;
    this.stopPeriodicChecking();

    // Resolve any ongoing desyncs
    this.resolveAllDesyncs('checking_stopped');

    this.dispatchEvent(new CustomEvent('checkingStopped', {
      detail: { roomId: this.state.roomId }
    }));

    console.log('🔄 Sync checking stopped');
  }

  /**
   * Manually trigger a sync check
   */
  checkSync(): void {
    if (!this.state.isActive) return;

    this.performSyncCheck();
  }

  /**
   * Update sync checker settings
   */
  updateSettings(settings: Partial<SyncCheckerState>): void {
    // Only allow safe updates
    const allowedKeys = ['checkInterval', 'toleranceMs', 'alertSettings'] as const;
    const safeSettings = Object.keys(settings)
      .filter(key => allowedKeys.includes(key as any))
      .reduce((obj, key) => {
        obj[key] = settings[key as keyof SyncCheckerState];
        return obj;
      }, {} as any);

    this.state = { ...this.state, ...safeSettings };

    // Restart checking if interval changed
    if (settings.checkInterval && this.state.isActive) {
      this.stopPeriodicChecking();
      this.startPeriodicChecking();
    }

    this.dispatchEvent(new CustomEvent('settingsUpdated', {
      detail: { settings: safeSettings }
    }));
  }

  /**
   * Get current sync checker state
   */
  getState(): SyncCheckerState {
    return { ...this.state };
  }

  /**
   * Get recent sync points
   */
  getSyncHistory(limit?: number): SyncPoint[] {
    const history = this.state.syncHistory;
    return limit ? history.slice(-limit) : history;
  }

  /**
   * Get active desync events
   */
  getActiveDesyncs(): DesyncEvent[] {
    return this.state.currentDesyncs.filter(d => !d.endTime);
  }

  /**
   * Get resolved desync events
   */
  getResolvedDesyncs(): DesyncEvent[] {
    return this.state.currentDesyncs.filter(d => d.endTime);
  }

  /**
   * Manually resolve a desync
   */
  resolveDesync(desyncId: string, method: string, description: string): void {
    const desync = this.state.currentDesyncs.find(d => d.id === desyncId);
    if (!desync || desync.endTime) return;

    desync.endTime = Date.now();
    desync.resolution = {
      method: method as any,
      timestamp: Date.now(),
      description
    };

    this.updateResolutionStats();

    this.dispatchEvent(new CustomEvent('desyncResolved', {
      detail: { desync }
    }));

    console.log(`🔄 Desync resolved: ${desyncId} via ${method}`);
  }

  /**
   * Clear sync history and reset stats
   */
  clearHistory(): void {
    this.state.syncHistory = [];
    this.state.currentDesyncs = [];
    this.state.totalChecks = 0;
    this.state.totalDesyncs = 0;
    this.state.averageResolutionTime = 0;

    this.dispatchEvent(new CustomEvent('historyCleared', {
      detail: { timestamp: Date.now() }
    }));

    console.log('🔄 Sync history cleared');
  }

  /**
   * Export sync checker data
   */
  exportData(): string {
    const exportData = {
      sessionInfo: {
        roomId: this.state.roomId,
        playerName: this.state.playerName,
        startTime: this.state.syncHistory[0]?.timestamp,
        endTime: this.state.syncHistory[this.state.syncHistory.length - 1]?.timestamp,
        totalChecks: this.state.totalChecks,
        totalDesyncs: this.state.totalDesyncs
      },
      syncHistory: this.state.syncHistory,
      desyncEvents: this.state.currentDesyncs,
      statistics: {
        totalChecks: this.state.totalChecks,
        totalDesyncs: this.state.totalDesyncs,
        averageResolutionTime: this.state.averageResolutionTime,
        successRate: this.state.totalChecks > 0 ? 
          ((this.state.totalChecks - this.state.totalDesyncs) / this.state.totalChecks * 100) : 100
      },
      settings: this.state.alertSettings,
      version: '1.0.0'
    };

    return JSON.stringify(exportData, null, 2);
  }

  /**
   * Destroy the sync checker
   */
  destroy(): void {
    this.isDestroyed = true;
    this.stopChecking();
    this.clearHistory();
    
    SyncChecker.instance = null;
    console.log('🔄 SyncChecker: Destroyed');
  }

  // ===== PRIVATE METHODS =====

  /**
   * Setup event listeners
   */
  private setupEventListeners(): void {
    // Listen to network events for backend state updates
    networkService.addEventListener('message', this.handleNetworkMessage.bind(this));
    
    // Listen to frontend state changes
    gameStore.subscribe(this.handleFrontendStateChange.bind(this));
  }

  /**
   * Handle incoming network messages
   */
  private handleNetworkMessage(event: Event): void {
    if (!this.state.isActive) return;

    const customEvent = event as CustomEvent<NetworkEventDetail>;
    const { roomId, message, data } = customEvent.detail;

    if (roomId !== this.state.roomId) return;

    // Update backend state when receiving phase_change or state updates
    if (message?.event === 'phase_change' || data?.phase) {
      this.lastBackendState = data || message?.data;
      
      // Trigger immediate sync check on important updates
      if (this.isCriticalUpdate(message?.event || '')) {
        this.performSyncCheck();
      }
    }
  }

  /**
   * Handle frontend state changes
   */
  private handleFrontendStateChange(newState: any): void {
    if (!this.state.isActive) return;

    // Trigger sync check when frontend state changes
    // Use debouncing to avoid excessive checks
    if (Date.now() - this.state.lastSyncCheck > 500) {
      this.performSyncCheck();
    }
  }

  /**
   * Start periodic sync checking
   */
  private startPeriodicChecking(): void {
    this.stopPeriodicChecking();
    
    this.checkTimer = setInterval(() => {
      if (this.state.isActive) {
        this.performSyncCheck();
      }
    }, this.state.checkInterval);
  }

  /**
   * Stop periodic sync checking
   */
  private stopPeriodicChecking(): void {
    if (this.checkTimer) {
      clearInterval(this.checkTimer);
      this.checkTimer = null;
    }
  }

  /**
   * Perform a sync check
   */
  private performSyncCheck(): void {
    const timestamp = Date.now();
    this.state.lastSyncCheck = timestamp;
    this.state.totalChecks++;

    const frontendState = gameStore.getState().gameState;
    const backendState = this.lastBackendState;

    if (!frontendState || !backendState) {
      return; // Not enough data to compare
    }

    const syncPoints: SyncPoint[] = [];
    const desyncFields: string[] = [];

    // Check each critical field
    for (const fieldPath of this.state.criticalFields) {
      const frontendValue = this.getValueAtPath(frontendState, fieldPath);
      const backendValue = this.getValueAtPath(backendState, fieldPath);
      
      const isSync = this.valuesAreInSync(frontendValue, backendValue, fieldPath);
      const severity = this.getSyncSeverity(fieldPath, !isSync);

      const syncPoint: SyncPoint = {
        id: crypto.randomUUID(),
        timestamp,
        fieldPath,
        frontendValue,
        backendValue,
        isSync,
        severity,
        context: {
          phase: frontendState.phase || 'unknown',
          playerName: this.state.playerName!,
          sequence: backendState.sequence,
          roomId: this.state.roomId!
        }
      };

      syncPoints.push(syncPoint);

      if (!isSync) {
        desyncFields.push(fieldPath);
      }
    }

    // Add sync points to history
    this.state.syncHistory.push(...syncPoints);
    
    // Limit history size
    if (this.state.syncHistory.length > 1000) {
      this.state.syncHistory = this.state.syncHistory.slice(-1000);
    }

    // Handle desyncs
    if (desyncFields.length > 0) {
      this.handleDesync(desyncFields, syncPoints, timestamp);
    } else {
      // Check if any existing desyncs should be auto-resolved
      this.checkAutoResolution();
    }

    this.dispatchEvent(new CustomEvent('syncCheckCompleted', {
      detail: { 
        syncPoints, 
        desyncFields,
        isSync: desyncFields.length === 0,
        timestamp 
      }
    }));
  }

  /**
   * Handle detected desyncs
   */
  private handleDesync(desyncFields: string[], syncPoints: SyncPoint[], timestamp: number): void {
    // Check if this is a continuation of existing desync
    const existingDesync = this.state.currentDesyncs.find(d => 
      !d.endTime && this.arraysOverlap(d.affectedFields, desyncFields)
    );

    if (existingDesync) {
      // Update existing desync
      existingDesync.affectedFields = Array.from(new Set([
        ...existingDesync.affectedFields,
        ...desyncFields
      ]));
      existingDesync.severity = this.calculateDesyncSeverity(existingDesync.affectedFields);
    } else {
      // Create new desync event
      const severity = this.calculateDesyncSeverity(desyncFields);
      const desyncEvent: DesyncEvent = {
        id: crypto.randomUUID(),
        timestamp,
        startTime: timestamp,
        affectedFields: desyncFields,
        severity,
        impact: this.calculateDesyncImpact(desyncFields, severity)
      };

      this.state.currentDesyncs.push(desyncEvent);
      this.state.totalDesyncs++;

      // Trigger alerts if enabled
      this.triggerDesyncAlert(desyncEvent);

      // Attempt auto-recovery if enabled
      if (this.state.alertSettings.enableAutoRecovery) {
        this.attemptAutoRecovery(desyncEvent);
      }

      this.dispatchEvent(new CustomEvent('desyncDetected', {
        detail: { desync: desyncEvent, syncPoints }
      }));

      console.warn(`🔄 Desync detected in fields: ${desyncFields.join(', ')} (${severity})`);
    }
  }

  /**
   * Check for auto-resolution of existing desyncs
   */
  private checkAutoResolution(): void {
    const activeDesyncs = this.getActiveDesyncs();
    
    for (const desync of activeDesyncs) {
      // Check if all fields are now in sync
      const stillDesync = desync.affectedFields.some(field => {
        const recent = this.state.syncHistory
          .filter(sp => sp.fieldPath === field)
          .slice(-3); // Check last 3 sync points for this field
        
        return recent.length > 0 && recent.every(sp => !sp.isSync);
      });

      if (!stillDesync) {
        this.resolveDesync(desync.id, 'auto_recovered', 'All affected fields returned to sync state');
      }
    }
  }

  /**
   * Trigger desync alert
   */
  private triggerDesyncAlert(desync: DesyncEvent): void {
    const { alertSettings } = this.state;
    
    // Check if we should alert for this severity
    if (alertSettings.criticalOnly && desync.severity !== 'critical') {
      return;
    }

    // Visual alert
    if (alertSettings.enableVisualAlerts) {
      this.dispatchEvent(new CustomEvent('desyncAlert', {
        detail: { 
          type: 'visual',
          desync,
          message: `Desync detected: ${desync.affectedFields.join(', ')}`
        }
      }));
    }

    // Audio alert
    if (alertSettings.enableAudioAlerts) {
      this.dispatchEvent(new CustomEvent('desyncAlert', {
        detail: { 
          type: 'audio',
          desync,
          urgency: desync.severity
        }
      }));
    }
  }

  /**
   * Attempt automatic recovery
   */
  private attemptAutoRecovery(desync: DesyncEvent): void {
    // For now, suggest manual actions
    // In the future, could implement automatic state refresh requests
    
    const recoveryActions = this.suggestRecoveryActions(desync);
    
    this.dispatchEvent(new CustomEvent('recoveryRequired', {
      detail: { 
        desync,
        suggestedActions: recoveryActions
      }
    }));
  }

  /**
   * Suggest recovery actions for a desync
   */
  private suggestRecoveryActions(desync: DesyncEvent): string[] {
    const actions: string[] = [];
    
    if (desync.affectedFields.includes('phase') || desync.affectedFields.includes('currentPlayer')) {
      actions.push('Request game state refresh from server');
      actions.push('Check network connection stability');
    }
    
    if (desync.affectedFields.includes('myHand') || desync.affectedFields.includes('players')) {
      actions.push('Refresh player data');
      actions.push('Verify WebSocket connection');
    }
    
    if (desync.severity === 'critical') {
      actions.push('Consider reconnecting to the game');
    }
    
    return actions;
  }

  /**
   * Resolve all active desyncs
   */
  private resolveAllDesyncs(reason: string): void {
    const activeDesyncs = this.getActiveDesyncs();
    
    for (const desync of activeDesyncs) {
      this.resolveDesync(desync.id, 'manual_fix', `Resolved due to: ${reason}`);
    }
  }

  /**
   * Update resolution time statistics
   */
  private updateResolutionStats(): void {
    const resolvedDesyncs = this.getResolvedDesyncs();
    
    if (resolvedDesyncs.length > 0) {
      const totalResolutionTime = resolvedDesyncs.reduce((sum, desync) => {
        return sum + (desync.endTime! - desync.startTime);
      }, 0);
      
      this.state.averageResolutionTime = totalResolutionTime / resolvedDesyncs.length;
    }
  }

  /**
   * Get value at object path
   */
  private getValueAtPath(obj: any, path: string): any {
    return path.split('.').reduce((current, key) => current?.[key], obj);
  }

  /**
   * Check if two values are in sync
   */
  private valuesAreInSync(frontendValue: any, backendValue: any, fieldPath: string): boolean {
    // Handle null/undefined
    if (frontendValue === null || frontendValue === undefined) {
      return backendValue === null || backendValue === undefined;
    }
    
    if (backendValue === null || backendValue === undefined) {
      return frontendValue === null || frontendValue === undefined;
    }

    // Handle timestamps with tolerance
    if (fieldPath.includes('timestamp') || fieldPath.includes('Time')) {
      const diff = Math.abs(frontendValue - backendValue);
      return diff <= this.state.toleranceMs;
    }

    // Handle arrays
    if (Array.isArray(frontendValue) && Array.isArray(backendValue)) {
      if (frontendValue.length !== backendValue.length) return false;
      
      for (let i = 0; i < frontendValue.length; i++) {
        if (!this.valuesAreInSync(frontendValue[i], backendValue[i], `${fieldPath}[${i}]`)) {
          return false;
        }
      }
      return true;
    }

    // Handle objects
    if (typeof frontendValue === 'object' && typeof backendValue === 'object') {
      const frontendKeys = Object.keys(frontendValue);
      const backendKeys = Object.keys(backendValue);
      
      if (frontendKeys.length !== backendKeys.length) return false;
      
      for (const key of frontendKeys) {
        if (!backendKeys.includes(key)) return false;
        if (!this.valuesAreInSync(frontendValue[key], backendValue[key], `${fieldPath}.${key}`)) {
          return false;
        }
      }
      return true;
    }

    // Handle primitives
    return frontendValue === backendValue;
  }

  /**
   * Get sync severity for a field
   */
  private getSyncSeverity(fieldPath: string, isDesync: boolean): SyncPoint['severity'] {
    if (!isDesync) return 'info';
    
    // Critical game state fields
    if (['phase', 'currentPlayer', 'gameOver'].includes(fieldPath)) {
      return 'critical';
    }
    
    // High impact fields
    if (['currentRound', 'turnNumber', 'myHand'].includes(fieldPath)) {
      return 'error';
    }
    
    // Medium impact fields
    if (['players', 'declarations', 'scores'].includes(fieldPath)) {
      return 'warning';
    }
    
    return 'info';
  }

  /**
   * Calculate overall desync severity
   */
  private calculateDesyncSeverity(fields: string[]): DesyncEvent['severity'] {
    if (fields.some(f => ['phase', 'currentPlayer', 'gameOver'].includes(f))) {
      return 'critical';
    }
    
    if (fields.some(f => ['currentRound', 'turnNumber', 'myHand'].includes(f))) {
      return 'high';
    }
    
    if (fields.some(f => ['players', 'declarations', 'scores'].includes(f))) {
      return 'medium';
    }
    
    return 'low';
  }

  /**
   * Calculate desync impact
   */
  private calculateDesyncImpact(fields: string[], severity: DesyncEvent['severity']): DesyncEvent['impact'] {
    const gameplayBlocking = fields.some(f => 
      ['phase', 'currentPlayer', 'gameOver', 'myHand'].includes(f)
    );
    
    let userExperienceImpact: DesyncEvent['impact']['userExperienceImpact'] = 'none';
    if (severity === 'critical') userExperienceImpact = 'severe';
    else if (severity === 'high') userExperienceImpact = 'major';
    else if (severity === 'medium') userExperienceImpact = 'minor';
    
    let dataIntegrity: DesyncEvent['impact']['dataIntegrity'] = 'safe';
    if (severity === 'critical') dataIntegrity = 'corrupted';
    else if (severity === 'high') dataIntegrity = 'risk';
    
    return {
      gameplayBlocking,
      userExperienceImpact,
      dataIntegrity
    };
  }

  /**
   * Check if two arrays have overlapping elements
   */
  private arraysOverlap(arr1: string[], arr2: string[]): boolean {
    return arr1.some(item => arr2.includes(item));
  }

  /**
   * Check if an update is critical and requires immediate sync check
   */
  private isCriticalUpdate(eventType: string): boolean {
    const criticalEvents = [
      'phase_change',
      'player_turn_start',
      'player_turn_end',
      'game_over',
      'round_start',
      'round_end'
    ];
    
    return criticalEvents.includes(eventType);
  }
}

// Export singleton instance
export const syncChecker = SyncChecker.getInstance();