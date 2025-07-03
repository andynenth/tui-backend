/**
 * 🎮 **useGameReplay Hook** - Phase 6.1 React Integration
 * 
 * React hook for game replay functionality:
 * ✅ Recording control (start/stop)
 * ✅ Playback control (play/pause/step/jump)
 * ✅ Event filtering and timeline navigation
 * ✅ Session import/export
 * ✅ Real-time state updates
 */

import { useState, useEffect, useCallback } from 'react';
import { gameReplayManager, type ReplaySession, type ReplayState, type ReplayEvent } from '../tools/GameReplay';

export interface GameReplayHook {
  // Recording
  startRecording: (roomId: string, playerName: string) => ReplaySession;
  stopRecording: () => ReplaySession | null;
  isRecording: boolean;

  // Playback
  startReplay: (session: ReplaySession) => void;
  stopReplay: () => void;
  togglePause: () => void;
  stepForward: () => void;
  stepBackward: () => void;
  jumpToEvent: (eventIndex: number) => void;
  setPlaybackSpeed: (speed: number) => void;

  // State
  replayState: ReplayState;
  currentSession: ReplaySession | null;
  filteredEvents: ReplayEvent[];
  
  // Timeline
  currentEventIndex: number;
  totalEvents: number;
  currentEvent: ReplayEvent | null;
  timelineProgress: number; // 0-1

  // Filters
  setEventFilters: (filters: Partial<ReplayState['eventFilters']>) => void;
  eventFilters: ReplayState['eventFilters'];

  // Import/Export
  exportSession: (session: ReplaySession) => string;
  importSession: (jsonData: string) => ReplaySession;
  
  // Session management
  sessions: ReplaySession[];
  saveSession: (session: ReplaySession) => void;
  loadSession: (sessionId: string) => ReplaySession | null;
  deleteSession: (sessionId: string) => void;
}

export const useGameReplay = (): GameReplayHook => {
  const [replayState, setReplayState] = useState<ReplayState>(gameReplayManager.getState());
  const [filteredEvents, setFilteredEvents] = useState<ReplayEvent[]>([]);
  const [sessions, setSessions] = useState<ReplaySession[]>([]);

  // Load saved sessions from localStorage on mount
  useEffect(() => {
    const savedSessions = loadSessionsFromStorage();
    setSessions(savedSessions);
  }, []);

  // Listen for replay state changes
  useEffect(() => {
    const handleStateChange = () => {
      const newState = gameReplayManager.getState();
      setReplayState(newState);
      setFilteredEvents(gameReplayManager.getFilteredEvents());
    };

    const handleRecordingStarted = (event: Event) => {
      handleStateChange();
    };

    const handleRecordingStopped = (event: Event) => {
      const customEvent = event as CustomEvent;
      const { session } = customEvent.detail;
      
      // Auto-save completed sessions
      saveSession(session);
      handleStateChange();
    };

    const handleReplayStarted = handleStateChange;
    const handleReplayStopped = handleStateChange;
    const handleReplayPauseToggled = handleStateChange;
    const handleReplayJumped = handleStateChange;
    const handlePlaybackSpeedChanged = handleStateChange;
    const handleFiltersChanged = handleStateChange;
    const handleEventRecorded = handleStateChange;
    const handleEventApplied = handleStateChange;

    // Add event listeners
    gameReplayManager.addEventListener('recordingStarted', handleRecordingStarted);
    gameReplayManager.addEventListener('recordingStopped', handleRecordingStopped);
    gameReplayManager.addEventListener('replayStarted', handleReplayStarted);
    gameReplayManager.addEventListener('replayStopped', handleReplayStopped);
    gameReplayManager.addEventListener('replayPauseToggled', handleReplayPauseToggled);
    gameReplayManager.addEventListener('replayJumped', handleReplayJumped);
    gameReplayManager.addEventListener('playbackSpeedChanged', handlePlaybackSpeedChanged);
    gameReplayManager.addEventListener('filtersChanged', handleFiltersChanged);
    gameReplayManager.addEventListener('eventRecorded', handleEventRecorded);
    gameReplayManager.addEventListener('eventApplied', handleEventApplied);

    // Initial state load
    handleStateChange();

    return () => {
      gameReplayManager.removeEventListener('recordingStarted', handleRecordingStarted);
      gameReplayManager.removeEventListener('recordingStopped', handleRecordingStopped);
      gameReplayManager.removeEventListener('replayStarted', handleReplayStarted);
      gameReplayManager.removeEventListener('replayStopped', handleReplayStopped);
      gameReplayManager.removeEventListener('replayPauseToggled', handleReplayPauseToggled);
      gameReplayManager.removeEventListener('replayJumped', handleReplayJumped);
      gameReplayManager.removeEventListener('playbackSpeedChanged', handlePlaybackSpeedChanged);
      gameReplayManager.removeEventListener('filtersChanged', handleFiltersChanged);
      gameReplayManager.removeEventListener('eventRecorded', handleEventRecorded);
      gameReplayManager.removeEventListener('eventApplied', handleEventApplied);
    };
  }, []);

  // Recording controls
  const startRecording = useCallback((roomId: string, playerName: string): ReplaySession => {
    return gameReplayManager.startRecording(roomId, playerName);
  }, []);

  const stopRecording = useCallback((): ReplaySession | null => {
    return gameReplayManager.stopRecording();
  }, []);

  // Playback controls
  const startReplay = useCallback((session: ReplaySession): void => {
    gameReplayManager.startReplay(session);
  }, []);

  const stopReplay = useCallback((): void => {
    gameReplayManager.stopReplay();
  }, []);

  const togglePause = useCallback((): void => {
    gameReplayManager.togglePause();
  }, []);

  const stepForward = useCallback((): void => {
    gameReplayManager.stepForward();
  }, []);

  const stepBackward = useCallback((): void => {
    gameReplayManager.stepBackward();
  }, []);

  const jumpToEvent = useCallback((eventIndex: number): void => {
    gameReplayManager.jumpToEvent(eventIndex);
  }, []);

  const setPlaybackSpeed = useCallback((speed: number): void => {
    gameReplayManager.setPlaybackSpeed(speed);
  }, []);

  // Filter controls
  const setEventFilters = useCallback((filters: Partial<ReplayState['eventFilters']>): void => {
    gameReplayManager.setEventFilters(filters);
  }, []);

  // Import/Export
  const exportSession = useCallback((session: ReplaySession): string => {
    return gameReplayManager.exportSession(session);
  }, []);

  const importSession = useCallback((jsonData: string): ReplaySession => {
    const session = gameReplayManager.importSession(jsonData);
    saveSession(session);
    return session;
  }, []);

  // Session management
  const saveSession = useCallback((session: ReplaySession): void => {
    setSessions(prevSessions => {
      const existingIndex = prevSessions.findIndex(s => s.id === session.id);
      let newSessions;
      
      if (existingIndex >= 0) {
        // Update existing session
        newSessions = [...prevSessions];
        newSessions[existingIndex] = session;
      } else {
        // Add new session
        newSessions = [...prevSessions, session];
      }

      // Save to localStorage
      saveSessionsToStorage(newSessions);
      return newSessions;
    });
  }, []);

  const loadSession = useCallback((sessionId: string): ReplaySession | null => {
    return sessions.find(s => s.id === sessionId) || null;
  }, [sessions]);

  const deleteSession = useCallback((sessionId: string): void => {
    setSessions(prevSessions => {
      const newSessions = prevSessions.filter(s => s.id !== sessionId);
      saveSessionsToStorage(newSessions);
      return newSessions;
    });
  }, []);

  // Computed values
  const currentSession = replayState.currentSession;
  const totalEvents = currentSession?.events.length || 0;
  const currentEventIndex = replayState.currentEventIndex;
  const currentEvent = currentSession?.events[currentEventIndex] || null;
  const timelineProgress = totalEvents > 0 ? currentEventIndex / (totalEvents - 1) : 0;

  return {
    // Recording
    startRecording,
    stopRecording,
    isRecording: replayState.isRecording,

    // Playback
    startReplay,
    stopReplay,
    togglePause,
    stepForward,
    stepBackward,
    jumpToEvent,
    setPlaybackSpeed,

    // State
    replayState,
    currentSession,
    filteredEvents,

    // Timeline
    currentEventIndex,
    totalEvents,
    currentEvent,
    timelineProgress,

    // Filters
    setEventFilters,
    eventFilters: replayState.eventFilters,

    // Import/Export
    exportSession,
    importSession,

    // Session management
    sessions,
    saveSession,
    loadSession,
    deleteSession
  };
};

// ===== HELPER FUNCTIONS =====

/**
 * Load sessions from localStorage
 */
function loadSessionsFromStorage(): ReplaySession[] {
  try {
    const stored = localStorage.getItem('gameReplaySessions');
    if (stored) {
      const sessions = JSON.parse(stored) as ReplaySession[];
      return Array.isArray(sessions) ? sessions : [];
    }
  } catch (error) {
    console.warn('Failed to load replay sessions from storage:', error);
  }
  return [];
}

/**
 * Save sessions to localStorage
 */
function saveSessionsToStorage(sessions: ReplaySession[]): void {
  try {
    localStorage.setItem('gameReplaySessions', JSON.stringify(sessions));
  } catch (error) {
    console.warn('Failed to save replay sessions to storage:', error);
  }
}

export default useGameReplay;