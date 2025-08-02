/**
 * Session Storage Tests
 *
 * Tests for session storage utility functions including:
 * - Session creation and storage
 * - Session retrieval and validation
 * - Session expiry handling
 * - Activity tracking
 * - Multi-session support
 * - Error handling and edge cases
 */

import {
  storeSession,
  updateSessionActivity,
  getSession,
  clearSession,
  hasValidSession,
  getSessionAge,
  getTimeSinceLastActivity,
  formatSessionInfo,
  storeMultiSession,
  getMultiSessions,
} from '../sessionStorage';

// Mock localStorage
const mockLocalStorage = {
  store: {},
  getItem: jest.fn((key) => mockLocalStorage.store[key] || null),
  setItem: jest.fn((key, value) => {
    mockLocalStorage.store[key] = value;
  }),
  removeItem: jest.fn((key) => {
    delete mockLocalStorage.store[key];
  }),
  clear: jest.fn(() => {
    mockLocalStorage.store = {};
  }),
};

// Mock console to avoid test output pollution
const mockConsole = {
  log: jest.fn(),
  error: jest.fn(),
};

describe('Session Storage Utilities', () => {
  let originalLocalStorage;
  let originalConsole;
  let originalDateNow;

  beforeEach(() => {
    // Clear storage first
    mockLocalStorage.store = {};
    
    // Clear all mocks
    jest.clearAllMocks();
    
    // Mock localStorage
    originalLocalStorage = global.localStorage;
    Object.defineProperty(global, 'localStorage', {
      value: mockLocalStorage,
      writable: true
    });

    // Mock console
    originalConsole = global.console;
    global.console = mockConsole;

    // Mock Date.now
    originalDateNow = Date.now;
    Date.now = jest.fn(() => 1000000); // Fixed timestamp
  });

  afterEach(() => {
    // Restore originals
    global.localStorage = originalLocalStorage;
    global.console = originalConsole;
    Date.now = originalDateNow;
  });

  describe('storeSession', () => {
    test('stores session data correctly', () => {
      storeSession('room123', 'Alice', 'session456', 'lobby');

      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'liap_tui_session',
        JSON.stringify({
          roomId: 'room123',
          playerName: 'Alice',
          sessionId: 'session456',
          createdAt: 1000000,
          lastActivity: 1000000,
          gamePhase: 'lobby',
        })
      );

      expect(mockConsole.log).toHaveBeenCalledWith(
        'Session stored:',
        { roomId: 'room123', playerName: 'Alice' }
      );
    });

    test('stores session with null gamePhase', () => {
      storeSession('room123', 'Alice', 'session456');

      const storedData = JSON.parse(mockLocalStorage.setItem.mock.calls[0][1]);
      expect(storedData.gamePhase).toBeNull();
    });

    test('handles localStorage errors gracefully', () => {
      mockLocalStorage.setItem.mockImplementationOnce(() => {
        throw new Error('Storage quota exceeded');
      });

      expect(() => {
        storeSession('room123', 'Alice', 'session456');
      }).not.toThrow();

      expect(mockConsole.error).toHaveBeenCalledWith(
        'Failed to store session:',
        expect.any(Error)
      );
    });

    test('stores with empty strings', () => {
      storeSession('', '', '', '');

      const storedData = JSON.parse(mockLocalStorage.setItem.mock.calls[0][1]);
      expect(storedData.roomId).toBe('');
      expect(storedData.playerName).toBe('');
      expect(storedData.sessionId).toBe('');
      expect(storedData.gamePhase).toBe('');
    });
  });

  describe('getSession', () => {
    test('retrieves stored session correctly', () => {
      const sessionData = {
        roomId: 'room123',
        playerName: 'Alice',
        sessionId: 'session456',
        createdAt: 1000000,
        lastActivity: 1000000,
        gamePhase: 'lobby',
      };

      mockLocalStorage.store['liap_tui_session'] = JSON.stringify(sessionData);

      const result = getSession();
      expect(result).toEqual(sessionData);
    });

    test('returns null when no session exists', () => {
      const result = getSession();
      expect(result).toBeNull();
    });

    test('returns null and clears expired session', () => {
      const expiredSession = {
        roomId: 'room123',
        playerName: 'Alice',
        sessionId: 'session456',
        createdAt: 1000000,
        lastActivity: 1000000 - (25 * 60 * 60 * 1000), // 25 hours ago
        gamePhase: 'lobby',
      };

      mockLocalStorage.store['liap_tui_session'] = JSON.stringify(expiredSession);

      const result = getSession();
      expect(result).toBeNull();
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('liap_tui_session');
    });

    test('handles corrupted session data', () => {
      mockLocalStorage.store['liap_tui_session'] = 'invalid json';

      const result = getSession();
      expect(result).toBeNull();
      expect(mockConsole.error).toHaveBeenCalledWith(
        'Failed to get session:',
        expect.any(Error)
      );
    });

    test('handles localStorage errors', () => {
      mockLocalStorage.getItem.mockImplementationOnce(() => {
        throw new Error('Storage access denied');
      });

      const result = getSession();
      expect(result).toBeNull();
      expect(mockConsole.error).toHaveBeenCalledWith(
        'Failed to get session:',
        expect.any(Error)
      );
    });

    test('validates session expiry correctly', () => {
      const almostExpiredSession = {
        roomId: 'room123',
        playerName: 'Alice',
        sessionId: 'session456',
        createdAt: 1000000,
        lastActivity: 1000000 - (23 * 60 * 60 * 1000), // 23 hours ago (still valid)
        gamePhase: 'lobby',
      };

      mockLocalStorage.store['liap_tui_session'] = JSON.stringify(almostExpiredSession);

      const result = getSession();
      expect(result).toEqual(almostExpiredSession);
      expect(mockLocalStorage.removeItem).not.toHaveBeenCalled();
    });
  });

  describe('updateSessionActivity', () => {
    test('updates activity timestamp for existing session', () => {
      const sessionData = {
        roomId: 'room123',
        playerName: 'Alice',
        sessionId: 'session456',
        createdAt: 1000000,
        lastActivity: 1000000,
        gamePhase: 'lobby',
      };

      mockLocalStorage.store['liap_tui_session'] = JSON.stringify(sessionData);

      Date.now = jest.fn(() => 2000000); // Later timestamp

      updateSessionActivity();

      const updatedSession = JSON.parse(mockLocalStorage.setItem.mock.calls[0][1]);
      expect(updatedSession.lastActivity).toBe(2000000);
      expect(updatedSession.createdAt).toBe(1000000); // Should not change
    });

    test('does nothing when no session exists', () => {
      updateSessionActivity();

      expect(mockLocalStorage.setItem).not.toHaveBeenCalled();
    });

    test('handles localStorage errors during update', () => {
      const sessionData = {
        roomId: 'room123',
        playerName: 'Alice',
        sessionId: 'session456',
        createdAt: 1000000,
        lastActivity: 1000000,
        gamePhase: 'lobby',
      };

      mockLocalStorage.store['liap_tui_session'] = JSON.stringify(sessionData);

      mockLocalStorage.setItem.mockImplementationOnce(() => {
        throw new Error('Storage error');
      });

      expect(() => updateSessionActivity()).not.toThrow();
      expect(mockConsole.error).toHaveBeenCalledWith(
        'Failed to update session activity:',
        expect.any(Error)
      );
    });
  });

  describe('clearSession', () => {
    test('removes session from localStorage', () => {
      mockLocalStorage.store['liap_tui_session'] = 'some data';

      clearSession();

      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('liap_tui_session');
      expect(mockConsole.log).toHaveBeenCalledWith('Session cleared');
    });

    test('handles localStorage errors during clear', () => {
      mockLocalStorage.removeItem.mockImplementationOnce(() => {
        throw new Error('Storage error');
      });

      expect(() => clearSession()).not.toThrow();
      expect(mockConsole.error).toHaveBeenCalledWith(
        'Failed to clear session:',
        expect.any(Error)
      );
    });
  });

  describe('hasValidSession', () => {
    test('returns true when valid session exists', () => {
      const sessionData = {
        roomId: 'room123',
        playerName: 'Alice',
        sessionId: 'session456',
        createdAt: 1000000,
        lastActivity: 1000000,
        gamePhase: 'lobby',
      };

      mockLocalStorage.store['liap_tui_session'] = JSON.stringify(sessionData);

      expect(hasValidSession()).toBe(true);
    });

    test('returns false when no session exists', () => {
      expect(hasValidSession()).toBe(false);
    });

    test('returns false when session is expired', () => {
      const expiredSession = {
        roomId: 'room123',
        playerName: 'Alice',
        sessionId: 'session456',
        createdAt: 1000000,
        lastActivity: 1000000 - (25 * 60 * 60 * 1000), // Expired
        gamePhase: 'lobby',
      };

      mockLocalStorage.store['liap_tui_session'] = JSON.stringify(expiredSession);

      expect(hasValidSession()).toBe(false);
    });
  });

  describe('getSessionAge', () => {
    test('returns correct session age', () => {
      const sessionData = {
        roomId: 'room123',
        playerName: 'Alice',
        sessionId: 'session456',
        createdAt: 500000,
        lastActivity: 1000000,
        gamePhase: 'lobby',
      };

      mockLocalStorage.store['liap_tui_session'] = JSON.stringify(sessionData);

      const age = getSessionAge();
      expect(age).toBe(500000); // 1000000 - 500000
    });

    test('returns null when no session exists', () => {
      const age = getSessionAge();
      expect(age).toBeNull();
    });
  });

  describe('getTimeSinceLastActivity', () => {
    test('returns correct time since last activity', () => {
      const sessionData = {
        roomId: 'room123',
        playerName: 'Alice',
        sessionId: 'session456',
        createdAt: 500000,
        lastActivity: 700000,
        gamePhase: 'lobby',
      };

      mockLocalStorage.store['liap_tui_session'] = JSON.stringify(sessionData);

      const timeSince = getTimeSinceLastActivity();
      expect(timeSince).toBe(300000); // 1000000 - 700000
    });

    test('returns null when no session exists', () => {
      const timeSince = getTimeSinceLastActivity();
      expect(timeSince).toBeNull();
    });
  });

  describe('formatSessionInfo', () => {
    test('formats session info correctly for recent activity', () => {
      const sessionData = {
        roomId: 'room123',
        playerName: 'Alice',
        sessionId: 'session456',
        createdAt: 1000000,
        lastActivity: 1000000 - 30000, // 30 seconds ago
        gamePhase: 'lobby',
      };

      mockLocalStorage.store['liap_tui_session'] = JSON.stringify(sessionData);

      const info = formatSessionInfo();
      expect(info).toEqual({
        roomId: 'room123',
        playerName: 'Alice',
        gamePhase: 'lobby',
        lastSeenText: 'Just now',
        isRecent: true,
      });
    });

    test('formats session info for activity minutes ago', () => {
      const sessionData = {
        roomId: 'room123',
        playerName: 'Alice',
        sessionId: 'session456',
        createdAt: 1000000,
        lastActivity: 1000000 - (3 * 60 * 1000), // 3 minutes ago
        gamePhase: 'turn',
      };

      mockLocalStorage.store['liap_tui_session'] = JSON.stringify(sessionData);

      const info = formatSessionInfo();
      expect(info).toEqual({
        roomId: 'room123',
        playerName: 'Alice',
        gamePhase: 'turn',
        lastSeenText: '3 minutes ago',
        isRecent: true,
      });
    });

    test('formats session info for old activity', () => {
      const sessionData = {
        roomId: 'room123',
        playerName: 'Alice',
        sessionId: 'session456',
        createdAt: 1000000,
        lastActivity: 1000000 - (10 * 60 * 1000), // 10 minutes ago
        gamePhase: 'scoring',
      };

      mockLocalStorage.store['liap_tui_session'] = JSON.stringify(sessionData);

      const info = formatSessionInfo();
      expect(info).toEqual({
        roomId: 'room123',
        playerName: 'Alice',
        gamePhase: 'scoring',
        lastSeenText: '10 minutes ago',
        isRecent: false,
      });
    });

    test('handles singular minute correctly', () => {
      const sessionData = {
        roomId: 'room123',
        playerName: 'Alice',
        sessionId: 'session456',
        createdAt: 1000000,
        lastActivity: 1000000 - (1 * 60 * 1000), // 1 minute ago
        gamePhase: 'declaration',
      };

      mockLocalStorage.store['liap_tui_session'] = JSON.stringify(sessionData);

      const info = formatSessionInfo();
      expect(info.lastSeenText).toBe('1 minute ago');
    });

    test('returns null when no session exists', () => {
      const info = formatSessionInfo();
      expect(info).toBeNull();
    });
  });

  describe('Multi-Session Support', () => {
    describe('storeMultiSession', () => {
      test('stores new session in multi-session array', () => {
        storeMultiSession('room123', 'Alice', 'session456');

        const stored = JSON.parse(mockLocalStorage.setItem.mock.calls[0][1]);
        expect(stored).toHaveLength(1);
        expect(stored[0]).toEqual({
          roomId: 'room123',
          playerName: 'Alice',
          sessionId: 'session456',
          createdAt: 1000000,
          lastActivity: 1000000,
        });
      });

      test('replaces existing session for same room', () => {
        // Store initial session
        const initialSessions = [
          {
            roomId: 'room123',
            playerName: 'Alice',
            sessionId: 'session456',
            createdAt: 900000,
            lastActivity: 900000,
          },
          {
            roomId: 'room999',
            playerName: 'Bob',
            sessionId: 'session789',
            createdAt: 950000,
            lastActivity: 950000,
          },
        ];

        mockLocalStorage.store['liap_tui_sessions'] = JSON.stringify(initialSessions);

        storeMultiSession('room123', 'Alice', 'newSession');

        const stored = JSON.parse(mockLocalStorage.setItem.mock.calls[0][1]);
        expect(stored).toHaveLength(2);
        
        const aliceSession = stored.find(s => s.roomId === 'room123');
        expect(aliceSession.sessionId).toBe('newSession');
        expect(aliceSession.createdAt).toBe(1000000);
        
        const bobSession = stored.find(s => s.roomId === 'room999');
        expect(bobSession).toEqual(initialSessions[1]);
      });

      test('limits sessions to last 5', () => {
        // Store 5 existing sessions
        const existingSessions = Array.from({ length: 5 }, (_, i) => ({
          roomId: `room${i}`,
          playerName: `Player${i}`,
          sessionId: `session${i}`,
          createdAt: 900000 + i * 1000,
          lastActivity: 900000 + i * 1000,
        }));

        mockLocalStorage.store['liap_tui_sessions'] = JSON.stringify(existingSessions);

        storeMultiSession('room999', 'NewPlayer', 'newSession');

        const stored = JSON.parse(mockLocalStorage.setItem.mock.calls[0][1]);
        expect(stored).toHaveLength(5);
        
        // Should have removed the oldest session (room0)
        expect(stored.find(s => s.roomId === 'room0')).toBeUndefined();
        expect(stored.find(s => s.roomId === 'room999')).toBeDefined();
      });

      test('handles localStorage errors gracefully', () => {
        mockLocalStorage.setItem.mockImplementationOnce(() => {
          throw new Error('Storage error');
        });

        expect(() => {
          storeMultiSession('room123', 'Alice', 'session456');
        }).not.toThrow();

        expect(mockConsole.error).toHaveBeenCalledWith(
          'Failed to store multi-session:',
          expect.any(Error)
        );
      });
    });

    describe('getMultiSessions', () => {
      test('returns all valid sessions', () => {
        const sessions = [
          {
            roomId: 'room123',
            playerName: 'Alice',
            sessionId: 'session456',
            createdAt: 1000000,
            lastActivity: 1000000,
          },
          {
            roomId: 'room999',
            playerName: 'Bob',
            sessionId: 'session789',
            createdAt: 1000000,
            lastActivity: 1000000,
          },
        ];

        mockLocalStorage.store['liap_tui_sessions'] = JSON.stringify(sessions);

        const result = getMultiSessions();
        expect(result).toEqual(sessions);
      });

      test('filters out expired sessions', () => {
        const sessions = [
          {
            roomId: 'room123',
            playerName: 'Alice',
            sessionId: 'session456',
            createdAt: 1000000,
            lastActivity: 1000000, // Current (valid)
          },
          {
            roomId: 'room999',
            playerName: 'Bob',
            sessionId: 'session789',
            createdAt: 500000,
            lastActivity: 1000000 - (25 * 60 * 60 * 1000), // Expired
          },
        ];

        mockLocalStorage.store['liap_tui_sessions'] = JSON.stringify(sessions);

        const result = getMultiSessions();
        expect(result).toHaveLength(1);
        expect(result[0].roomId).toBe('room123');
      });

      test('returns empty array when no sessions exist', () => {
        const result = getMultiSessions();
        expect(result).toEqual([]);
      });

      test('handles corrupted data gracefully', () => {
        mockLocalStorage.store['liap_tui_sessions'] = 'invalid json';

        const result = getMultiSessions();
        expect(result).toEqual([]);
        expect(mockConsole.error).toHaveBeenCalledWith(
          'Failed to get multi-sessions:',
          expect.any(Error)
        );
      });

      test('handles localStorage errors', () => {
        mockLocalStorage.getItem.mockImplementationOnce(() => {
          throw new Error('Storage error');
        });

        const result = getMultiSessions();
        expect(result).toEqual([]);
        expect(mockConsole.error).toHaveBeenCalledWith(
          'Failed to get multi-sessions:',
          expect.any(Error)
        );
      });
    });
  });

  describe('Edge Cases and Error Handling', () => {
    test('handles undefined localStorage', () => {
      // Functions should handle undefined localStorage gracefully (not throw)
      const originalLS = global.localStorage;
      global.localStorage = undefined;
      
      expect(() => {
        storeSession('room', 'player', 'session');
      }).not.toThrow();
      
      expect(() => {
        getSession();
      }).not.toThrow();
      
      expect(() => {
        clearSession();
      }).not.toThrow();
      
      global.localStorage = originalLS;
    });

    test('handles null parameters gracefully', () => {
      expect(() => {
        storeSession(null, null, null, null);
      }).not.toThrow();

      const stored = JSON.parse(mockLocalStorage.setItem.mock.calls[0][1]);
      expect(stored.roomId).toBeNull();
      expect(stored.playerName).toBeNull();
      expect(stored.sessionId).toBeNull();
      expect(stored.gamePhase).toBeNull();
    });

    test('handles session with missing fields', () => {
      const incompleteSession = {
        roomId: 'room123',
        // Missing other fields
      };

      mockLocalStorage.store['liap_tui_session'] = JSON.stringify(incompleteSession);

      expect(() => getSession()).not.toThrow();
      expect(() => getSessionAge()).not.toThrow();
      expect(() => formatSessionInfo()).not.toThrow();
    });

    test('maintains consistency across function calls', () => {
      // Store a session
      storeSession('room123', 'Alice', 'session456', 'lobby');

      // Verify it exists
      expect(hasValidSession()).toBe(true);

      // Get the session
      const session = getSession();
      expect(session).toBeTruthy();
      expect(session.roomId).toBe('room123');

      // Update activity
      Date.now = jest.fn(() => 2000000);
      updateSessionActivity();

      // Verify update
      const updatedSession = getSession();
      expect(updatedSession.lastActivity).toBe(2000000);

      // Clear session
      clearSession();

      // Verify cleared
      expect(hasValidSession()).toBe(false);
      expect(getSession()).toBeNull();
    });
  });
});