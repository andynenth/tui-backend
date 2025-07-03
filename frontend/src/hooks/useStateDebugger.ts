/**
 * 🔍 **useStateDebugger Hook** - Phase 6.2 React Integration
 * 
 * React hook for state debugging functionality:
 * ✅ Live state monitoring controls
 * ✅ State comparison and diff viewing
 * ✅ WebSocket message filtering and viewing
 * ✅ Performance metrics tracking
 * ✅ Real-time updates and notifications
 */

import { useState, useEffect, useCallback } from 'react';
import { stateDebugger, type DebuggerState, type StateSnapshot, type StateDifference, type WebSocketMessage, type PerformanceMetrics } from '../tools/StateDebugger';

export interface StateDebuggerHook {
  // Control
  startDebugging: (roomId: string, playerName: string) => void;
  stopDebugging: () => void;
  captureState: () => void;
  clearData: () => void;

  // State
  debuggerState: DebuggerState;
  isActive: boolean;
  
  // State snapshots
  stateHistory: StateSnapshot[];
  currentFrontendState: any;
  currentBackendState: any;
  stateDifferences: StateDifference[];
  
  // Messages
  recentMessages: WebSocketMessage[];
  filteredMessages: WebSocketMessage[];
  setMessageFilters: (filters: Partial<DebuggerState['messageFilters']>) => void;
  
  // Performance
  performanceMetrics: PerformanceMetrics;
  
  // View options
  viewOptions: DebuggerState['viewOptions'];
  setViewOptions: (options: Partial<DebuggerState['viewOptions']>) => void;
  
  // Data export
  exportData: () => string;
  
  // Statistics
  totalSnapshots: number;
  totalMessages: number;
  criticalDifferences: number;
  averageLatency: number;
}

export const useStateDebugger = (): StateDebuggerHook => {
  const [debuggerState, setDebuggerState] = useState<DebuggerState>(stateDebugger.getState());
  const [stateHistory, setStateHistory] = useState<StateSnapshot[]>([]);
  const [filteredMessages, setFilteredMessages] = useState<WebSocketMessage[]>([]);

  // Listen for debugger events
  useEffect(() => {
    const handleStateUpdate = () => {
      const newState = stateDebugger.getState();
      setDebuggerState(newState);
      setStateHistory(stateDebugger.getStateHistory());
      setFilteredMessages(stateDebugger.getFilteredMessages());
    };

    const handleDebuggingStarted = (event: Event) => {
      console.log('🔍 State debugging started');
      handleStateUpdate();
    };

    const handleDebuggingStopped = (event: Event) => {
      console.log('🔍 State debugging stopped');
      handleStateUpdate();
    };

    const handleStateUpdated = (event: Event) => {
      handleStateUpdate();
    };

    const handleBackendStateUpdated = (event: Event) => {
      handleStateUpdate();
    };

    const handleStateDifferencesFound = (event: Event) => {
      const customEvent = event as CustomEvent;
      const { differences, count } = customEvent.detail;
      
      // Notify about critical differences
      const criticalDiffs = differences.filter((d: StateDifference) => d.severity === 'critical');
      if (criticalDiffs.length > 0) {
        console.warn(`🔍 Found ${criticalDiffs.length} critical state differences:`, criticalDiffs);
      }
      
      handleStateUpdate();
    };

    const handleDataCleared = (event: Event) => {
      handleStateUpdate();
    };

    const handleFiltersChanged = (event: Event) => {
      setFilteredMessages(stateDebugger.getFilteredMessages());
    };

    const handleViewOptionsChanged = (event: Event) => {
      handleStateUpdate();
    };

    // Add event listeners
    stateDebugger.addEventListener('debuggingStarted', handleDebuggingStarted);
    stateDebugger.addEventListener('debuggingStopped', handleDebuggingStopped);
    stateDebugger.addEventListener('stateUpdated', handleStateUpdated);
    stateDebugger.addEventListener('backendStateUpdated', handleBackendStateUpdated);
    stateDebugger.addEventListener('stateDifferencesFound', handleStateDifferencesFound);
    stateDebugger.addEventListener('dataCleared', handleDataCleared);
    stateDebugger.addEventListener('filtersChanged', handleFiltersChanged);
    stateDebugger.addEventListener('viewOptionsChanged', handleViewOptionsChanged);

    // Initial state load
    handleStateUpdate();

    return () => {
      stateDebugger.removeEventListener('debuggingStarted', handleDebuggingStarted);
      stateDebugger.removeEventListener('debuggingStopped', handleDebuggingStopped);
      stateDebugger.removeEventListener('stateUpdated', handleStateUpdated);
      stateDebugger.removeEventListener('backendStateUpdated', handleBackendStateUpdated);
      stateDebugger.removeEventListener('stateDifferencesFound', handleStateDifferencesFound);
      stateDebugger.removeEventListener('dataCleared', handleDataCleared);
      stateDebugger.removeEventListener('filtersChanged', handleFiltersChanged);
      stateDebugger.removeEventListener('viewOptionsChanged', handleViewOptionsChanged);
    };
  }, []);

  // Control functions
  const startDebugging = useCallback((roomId: string, playerName: string): void => {
    stateDebugger.startDebugging(roomId, playerName);
  }, []);

  const stopDebugging = useCallback((): void => {
    stateDebugger.stopDebugging();
  }, []);

  const captureState = useCallback((): void => {
    stateDebugger.captureCurrentState();
  }, []);

  const clearData = useCallback((): void => {
    stateDebugger.clearData();
  }, []);

  // Filter and option functions
  const setMessageFilters = useCallback((filters: Partial<DebuggerState['messageFilters']>): void => {
    stateDebugger.setMessageFilters(filters);
  }, []);

  const setViewOptions = useCallback((options: Partial<DebuggerState['viewOptions']>): void => {
    stateDebugger.setViewOptions(options);
  }, []);

  // Export function
  const exportData = useCallback((): string => {
    return stateDebugger.exportData();
  }, []);

  // Computed values
  const isActive = debuggerState.isActive;
  const currentFrontendState = debuggerState.frontendState;
  const currentBackendState = debuggerState.backendState;
  const stateDifferences = debuggerState.stateDifferences;
  const recentMessages = debuggerState.recentMessages;
  const performanceMetrics = debuggerState.performanceMetrics;
  const viewOptions = debuggerState.viewOptions;

  // Statistics
  const totalSnapshots = stateHistory.length;
  const totalMessages = recentMessages.length;
  const criticalDifferences = stateDifferences.filter(d => d.severity === 'critical').length;
  const averageLatency = performanceMetrics.stateUpdateLatency.average;

  return {
    // Control
    startDebugging,
    stopDebugging,
    captureState,
    clearData,

    // State
    debuggerState,
    isActive,

    // State snapshots
    stateHistory,
    currentFrontendState,
    currentBackendState,
    stateDifferences,

    // Messages
    recentMessages,
    filteredMessages,
    setMessageFilters,

    // Performance
    performanceMetrics,

    // View options
    viewOptions,
    setViewOptions,

    // Data export
    exportData,

    // Statistics
    totalSnapshots,
    totalMessages,
    criticalDifferences,
    averageLatency
  };
};

export default useStateDebugger;