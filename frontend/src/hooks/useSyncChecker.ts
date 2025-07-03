/**
 * 🔄 **useSyncChecker Hook** - Phase 6.3 React Integration
 * 
 * React hook for sync checker functionality:
 * ✅ Desync monitoring controls
 * ✅ Real-time sync status and alerts
 * ✅ Desync event tracking and resolution
 * ✅ Performance statistics and history
 * ✅ Alert configuration and management
 */

import { useState, useEffect, useCallback } from 'react';
import { syncChecker, type SyncCheckerState, type SyncPoint, type DesyncEvent } from '../tools/SyncChecker';

export interface SyncCheckerHook {
  // Control
  startChecking: (roomId: string, playerName: string) => void;
  stopChecking: () => void;
  checkSync: () => void;
  updateSettings: (settings: Partial<SyncCheckerState>) => void;
  
  // State
  syncState: SyncCheckerState;
  isActive: boolean;
  
  // Sync data
  syncHistory: SyncPoint[];
  activeDesyncs: DesyncEvent[];
  resolvedDesyncs: DesyncEvent[];
  
  // Current status
  currentSyncStatus: 'synced' | 'warning' | 'desync' | 'critical';
  lastCheckTime: number;
  
  // Statistics
  totalChecks: number;
  totalDesyncs: number;
  averageResolutionTime: number;
  successRate: number;
  
  // Actions
  resolveDesync: (desyncId: string, method: string, description: string) => void;
  clearHistory: () => void;
  exportData: () => string;
  
  // Alerts
  activeAlerts: {
    id: string;
    type: 'visual' | 'audio';
    message: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    timestamp: number;
  }[];
  dismissAlert: (alertId: string) => void;
}

export const useSyncChecker = (): SyncCheckerHook => {
  const [syncState, setSyncState] = useState<SyncCheckerState>(syncChecker.getState());
  const [syncHistory, setSyncHistory] = useState<SyncPoint[]>([]);
  const [activeDesyncs, setActiveDesyncs] = useState<DesyncEvent[]>([]);
  const [resolvedDesyncs, setResolvedDesyncs] = useState<DesyncEvent[]>([]);
  const [activeAlerts, setActiveAlerts] = useState<{
    id: string;
    type: 'visual' | 'audio';
    message: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    timestamp: number;
  }[]>([]);

  // Listen for sync checker events
  useEffect(() => {
    const handleCheckingStarted = () => {
      const newState = syncChecker.getState();
      setSyncState(newState);
      console.log('🔄 Sync checking started');
    };

    const handleCheckingStopped = () => {
      const newState = syncChecker.getState();
      setSyncState(newState);
      console.log('🔄 Sync checking stopped');
    };

    const handleSyncCheckCompleted = (event: Event) => {
      const customEvent = event as CustomEvent;
      const { syncPoints, desyncFields, isSync } = customEvent.detail;
      
      const newState = syncChecker.getState();
      setSyncState(newState);
      setSyncHistory(syncChecker.getSyncHistory(100)); // Keep last 100 points
      setActiveDesyncs(syncChecker.getActiveDesyncs());
      setResolvedDesyncs(syncChecker.getResolvedDesyncs());
      
      // Log sync status
      if (!isSync) {
        console.warn(`🔄 Desync detected in: ${desyncFields.join(', ')}`);
      }
    };

    const handleDesyncDetected = (event: Event) => {
      const customEvent = event as CustomEvent;
      const { desync } = customEvent.detail;
      
      setActiveDesyncs(syncChecker.getActiveDesyncs());
      console.warn(`🔄 New desync: ${desync.id} affecting ${desync.affectedFields.join(', ')}`);
    };

    const handleDesyncResolved = (event: Event) => {
      const customEvent = event as CustomEvent;
      const { desync } = customEvent.detail;
      
      setActiveDesyncs(syncChecker.getActiveDesyncs());
      setResolvedDesyncs(syncChecker.getResolvedDesyncs());
      console.log(`🔄 Desync resolved: ${desync.id}`);
    };

    const handleDesyncAlert = (event: Event) => {
      const customEvent = event as CustomEvent;
      const { type, desync, message, urgency } = customEvent.detail;
      
      const alert = {
        id: crypto.randomUUID(),
        type,
        message: message || `Desync in ${desync.affectedFields.join(', ')}`,
        severity: urgency || desync.severity,
        timestamp: Date.now()
      };
      
      setActiveAlerts(prev => [...prev, alert]);
      
      // Auto-dismiss alerts after 10 seconds
      setTimeout(() => {
        setActiveAlerts(prev => prev.filter(a => a.id !== alert.id));
      }, 10000);
      
      // Play audio alert if enabled
      if (type === 'audio') {
        // Could play different sounds based on urgency
        console.log(`🔄 Audio alert: ${urgency} desync detected`);
      }
    };

    const handleRecoveryRequired = (event: Event) => {
      const customEvent = event as CustomEvent;
      const { desync, suggestedActions } = customEvent.detail;
      
      console.log(`🔄 Recovery required for desync ${desync.id}:`, suggestedActions);
      
      // Create recovery alert
      const recoveryAlert = {
        id: crypto.randomUUID(),
        type: 'visual' as const,
        message: `Recovery needed: ${suggestedActions[0] || 'Manual intervention required'}`,
        severity: desync.severity,
        timestamp: Date.now()
      };
      
      setActiveAlerts(prev => [...prev, recoveryAlert]);
    };

    const handleSettingsUpdated = () => {
      const newState = syncChecker.getState();
      setSyncState(newState);
    };

    const handleHistoryCleared = () => {
      setSyncHistory([]);
      setActiveDesyncs([]);
      setResolvedDesyncs([]);
      const newState = syncChecker.getState();
      setSyncState(newState);
    };

    // Add event listeners
    syncChecker.addEventListener('checkingStarted', handleCheckingStarted);
    syncChecker.addEventListener('checkingStopped', handleCheckingStopped);
    syncChecker.addEventListener('syncCheckCompleted', handleSyncCheckCompleted);
    syncChecker.addEventListener('desyncDetected', handleDesyncDetected);
    syncChecker.addEventListener('desyncResolved', handleDesyncResolved);
    syncChecker.addEventListener('desyncAlert', handleDesyncAlert);
    syncChecker.addEventListener('recoveryRequired', handleRecoveryRequired);
    syncChecker.addEventListener('settingsUpdated', handleSettingsUpdated);
    syncChecker.addEventListener('historyCleared', handleHistoryCleared);

    // Initial state load
    setSyncState(syncChecker.getState());
    setSyncHistory(syncChecker.getSyncHistory(100));
    setActiveDesyncs(syncChecker.getActiveDesyncs());
    setResolvedDesyncs(syncChecker.getResolvedDesyncs());

    return () => {
      syncChecker.removeEventListener('checkingStarted', handleCheckingStarted);
      syncChecker.removeEventListener('checkingStopped', handleCheckingStopped);
      syncChecker.removeEventListener('syncCheckCompleted', handleSyncCheckCompleted);
      syncChecker.removeEventListener('desyncDetected', handleDesyncDetected);
      syncChecker.removeEventListener('desyncResolved', handleDesyncResolved);
      syncChecker.removeEventListener('desyncAlert', handleDesyncAlert);
      syncChecker.removeEventListener('recoveryRequired', handleRecoveryRequired);
      syncChecker.removeEventListener('settingsUpdated', handleSettingsUpdated);
      syncChecker.removeEventListener('historyCleared', handleHistoryCleared);
    };
  }, []);

  // Control functions
  const startChecking = useCallback((roomId: string, playerName: string): void => {
    syncChecker.startChecking(roomId, playerName);
  }, []);

  const stopChecking = useCallback((): void => {
    syncChecker.stopChecking();
  }, []);

  const checkSync = useCallback((): void => {
    syncChecker.checkSync();
  }, []);

  const updateSettings = useCallback((settings: Partial<SyncCheckerState>): void => {
    syncChecker.updateSettings(settings);
  }, []);

  const resolveDesync = useCallback((desyncId: string, method: string, description: string): void => {
    syncChecker.resolveDesync(desyncId, method, description);
  }, []);

  const clearHistory = useCallback((): void => {
    syncChecker.clearHistory();
  }, []);

  const exportData = useCallback((): string => {
    return syncChecker.exportData();
  }, []);

  const dismissAlert = useCallback((alertId: string): void => {
    setActiveAlerts(prev => prev.filter(alert => alert.id !== alertId));
  }, []);

  // Computed values
  const isActive = syncState.isActive;
  const lastCheckTime = syncState.lastSyncCheck;
  const totalChecks = syncState.totalChecks;
  const totalDesyncs = syncState.totalDesyncs;
  const averageResolutionTime = syncState.averageResolutionTime;
  
  // Calculate success rate
  const successRate = totalChecks > 0 ? 
    ((totalChecks - totalDesyncs) / totalChecks * 100) : 100;

  // Determine current sync status
  const currentSyncStatus: 'synced' | 'warning' | 'desync' | 'critical' = (() => {
    const criticalDesyncs = activeDesyncs.filter(d => d.severity === 'critical');
    const highDesyncs = activeDesyncs.filter(d => d.severity === 'high');
    
    if (criticalDesyncs.length > 0) return 'critical';
    if (highDesyncs.length > 0) return 'desync';
    if (activeDesyncs.length > 0) return 'warning';
    return 'synced';
  })();

  return {
    // Control
    startChecking,
    stopChecking,
    checkSync,
    updateSettings,
    
    // State
    syncState,
    isActive,
    
    // Sync data
    syncHistory,
    activeDesyncs,
    resolvedDesyncs,
    
    // Current status
    currentSyncStatus,
    lastCheckTime,
    
    // Statistics
    totalChecks,
    totalDesyncs,
    averageResolutionTime,
    successRate,
    
    // Actions
    resolveDesync,
    clearHistory,
    exportData,
    
    // Alerts
    activeAlerts,
    dismissAlert
  };
};

export default useSyncChecker;