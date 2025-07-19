// frontend/src/utils/sessionStorage.js

/**
 * Session storage utilities for browser close handling
 * Stores session info to allow reconnection after browser refresh/close
 */

import { generateReconnectionUrl } from './reconnectionUrl';

const SESSION_KEY = 'liap_tui_session';
const SESSION_EXPIRY_HOURS = 24;

/**
 * Session data structure
 * @typedef {Object} SessionData
 * @property {string} roomId - The room ID
 * @property {string} playerName - The player's name
 * @property {string} sessionId - Unique session identifier
 * @property {number} createdAt - Timestamp when session was created
 * @property {number} lastActivity - Last activity timestamp
 * @property {string} gamePhase - Current game phase when disconnected
 */

/**
 * Store session data
 */
export function storeSession(roomId, playerName, sessionId, gamePhase = null) {
  const sessionData = {
    roomId,
    playerName,
    sessionId,
    createdAt: Date.now(),
    lastActivity: Date.now(),
    gamePhase,
    reconnectionUrl: generateReconnectionUrl(roomId, playerName),
  };

  try {
    localStorage.setItem(SESSION_KEY, JSON.stringify(sessionData));
    console.log('Session stored:', {
      roomId,
      playerName,
      reconnectionUrl: sessionData.reconnectionUrl,
    });
  } catch (error) {
    console.error('Failed to store session:', error);
  }
}

/**
 * Update session activity timestamp
 */
export function updateSessionActivity() {
  const session = getSession();
  if (session) {
    session.lastActivity = Date.now();
    try {
      localStorage.setItem(SESSION_KEY, JSON.stringify(session));
    } catch (error) {
      console.error('Failed to update session activity:', error);
    }
  }
}

/**
 * Get stored session
 */
export function getSession() {
  try {
    const sessionStr = localStorage.getItem(SESSION_KEY);
    if (!sessionStr) return null;

    const session = JSON.parse(sessionStr);

    // Check if session is expired
    const expiryTime = SESSION_EXPIRY_HOURS * 60 * 60 * 1000;
    const isExpired = Date.now() - session.lastActivity > expiryTime;

    if (isExpired) {
      clearSession();
      return null;
    }

    return session;
  } catch (error) {
    console.error('Failed to get session:', error);
    return null;
  }
}

/**
 * Clear session data
 */
export function clearSession() {
  try {
    localStorage.removeItem(SESSION_KEY);
    console.log('Session cleared');
  } catch (error) {
    console.error('Failed to clear session:', error);
  }
}

/**
 * Check if there's a valid session for reconnection
 */
export function hasValidSession() {
  const session = getSession();
  return session !== null;
}

/**
 * Get session age in milliseconds
 */
export function getSessionAge() {
  const session = getSession();
  if (!session) return null;

  return Date.now() - session.createdAt;
}

/**
 * Get time since last activity in milliseconds
 */
export function getTimeSinceLastActivity() {
  const session = getSession();
  if (!session) return null;

  return Date.now() - session.lastActivity;
}

/**
 * Format session for display
 */
export function formatSessionInfo() {
  const session = getSession();
  if (!session) return null;

  const timeSinceActivity = getTimeSinceLastActivity();
  const minutesAgo = Math.floor(timeSinceActivity / 60000);

  return {
    roomId: session.roomId,
    playerName: session.playerName,
    gamePhase: session.gamePhase,
    lastSeenText:
      minutesAgo < 1
        ? 'Just now'
        : `${minutesAgo} minute${minutesAgo > 1 ? 's' : ''} ago`,
    isRecent: minutesAgo < 5,
  };
}

/**
 * Store multiple sessions (for multi-game support in future)
 */
const SESSIONS_KEY = 'liap_tui_sessions';

export function storeMultiSession(roomId, playerName, sessionId) {
  try {
    const sessionsStr = localStorage.getItem(SESSIONS_KEY) || '[]';
    const sessions = JSON.parse(sessionsStr);

    // Remove existing session for same room
    const filtered = sessions.filter((s) => s.roomId !== roomId);

    // Add new session
    filtered.push({
      roomId,
      playerName,
      sessionId,
      createdAt: Date.now(),
      lastActivity: Date.now(),
    });

    // Keep only last 5 sessions
    const recent = filtered.slice(-5);

    localStorage.setItem(SESSIONS_KEY, JSON.stringify(recent));
  } catch (error) {
    console.error('Failed to store multi-session:', error);
  }
}

export function getMultiSessions() {
  try {
    const sessionsStr = localStorage.getItem(SESSIONS_KEY) || '[]';
    const sessions = JSON.parse(sessionsStr);

    // Filter out expired sessions
    const expiryTime = SESSION_EXPIRY_HOURS * 60 * 60 * 1000;
    const valid = sessions.filter(
      (s) => Date.now() - s.lastActivity < expiryTime
    );

    return valid;
  } catch (error) {
    console.error('Failed to get multi-sessions:', error);
    return [];
  }
}
