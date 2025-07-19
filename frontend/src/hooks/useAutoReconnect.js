// frontend/src/hooks/useAutoReconnect.js

import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { networkService } from '../services/NetworkService';
import { 
  getSession, 
  clearSession, 
  storeSession, 
  updateSessionActivity 
} from '../utils/sessionStorage';
import { tabCommunication } from '../utils/tabCommunication';

/**
 * Hook for handling automatic reconnection after browser close/refresh
 */
const useAutoReconnect = () => {
  const navigate = useNavigate();
  const [reconnectState, setReconnectState] = useState({
    checking: true,
    hasSession: false,
    sessionInfo: null,
    duplicateTab: false,
    reconnecting: false,
    error: null,
  });

  // Check for existing session on mount
  useEffect(() => {
    const checkSession = async () => {
      try {
        const session = getSession();
        
        if (!session) {
          setReconnectState(prev => ({
            ...prev,
            checking: false,
            hasSession: false,
          }));
          return;
        }

        // Initialize tab communication
        tabCommunication.init(session.roomId, session.playerName);

        // Check for duplicate tabs
        const duplicates = await tabCommunication.checkForDuplicates(
          session.roomId, 
          session.playerName
        );

        if (duplicates.length > 0) {
          setReconnectState(prev => ({
            ...prev,
            checking: false,
            hasSession: true,
            sessionInfo: session,
            duplicateTab: true,
          }));
          return;
        }

        setReconnectState(prev => ({
          ...prev,
          checking: false,
          hasSession: true,
          sessionInfo: session,
          duplicateTab: false,
        }));

      } catch (error) {
        console.error('Error checking session:', error);
        setReconnectState(prev => ({
          ...prev,
          checking: false,
          error: error.message,
        }));
      }
    };

    checkSession();
  }, []);

  // Set up activity tracking
  useEffect(() => {
    if (!reconnectState.hasSession) return;

    const updateActivity = () => updateSessionActivity();
    
    // Update on user activity
    const events = ['mousedown', 'keydown', 'touchstart', 'scroll'];
    events.forEach(event => {
      window.addEventListener(event, updateActivity);
    });

    // Update periodically
    const interval = setInterval(updateActivity, 60000); // Every minute

    return () => {
      events.forEach(event => {
        window.removeEventListener(event, updateActivity);
      });
      clearInterval(interval);
    };
  }, [reconnectState.hasSession]);

  /**
   * Attempt to reconnect to the game
   */
  const reconnect = useCallback(async () => {
    if (!reconnectState.sessionInfo) return;

    setReconnectState(prev => ({ ...prev, reconnecting: true, error: null }));

    try {
      const { roomId, playerName } = reconnectState.sessionInfo;

      // Connect to room
      await networkService.connectToRoom(roomId);

      // Send client_ready with player name for reconnection
      networkService.send(roomId, 'client_ready', { 
        player_name: playerName,
        reconnecting: true,
      });

      // Navigate to game
      navigate(`/game/${roomId}`);

      // Session will be updated by the game component
    } catch (error) {
      console.error('Reconnection failed:', error);
      setReconnectState(prev => ({
        ...prev,
        reconnecting: false,
        error: error.message,
      }));
    }
  }, [reconnectState.sessionInfo, navigate]);

  /**
   * Join as new player (clear session and continue)
   */
  const joinAsNew = useCallback(() => {
    clearSession();
    tabCommunication.cleanup();
    setReconnectState({
      checking: false,
      hasSession: false,
      sessionInfo: null,
      duplicateTab: false,
      reconnecting: false,
      error: null,
    });
  }, []);

  /**
   * Store new session
   */
  const createSession = useCallback((roomId, playerName, gamePhase = null) => {
    const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    storeSession(roomId, playerName, sessionId, gamePhase);
    tabCommunication.init(roomId, playerName);
  }, []);

  /**
   * Update session phase
   */
  const updateSessionPhase = useCallback((gamePhase) => {
    const session = getSession();
    if (session) {
      storeSession(
        session.roomId, 
        session.playerName, 
        session.sessionId, 
        gamePhase
      );
    }
  }, []);

  return {
    ...reconnectState,
    reconnect,
    joinAsNew,
    createSession,
    updateSessionPhase,
    clearSession: () => {
      clearSession();
      tabCommunication.cleanup();
    },
  };
};

export default useAutoReconnect;