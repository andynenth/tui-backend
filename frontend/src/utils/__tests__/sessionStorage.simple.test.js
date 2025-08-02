/**
 * Session Storage Simple Tests
 * 
 * Simplified tests focusing on core functionality
 */

import {
  storeSession,
  getSession,
  clearSession,
  hasValidSession,
} from '../sessionStorage';

// Simple localStorage mock
Object.defineProperty(window, 'localStorage', {
  value: {
    store: {},
    getItem: jest.fn(function(key) { return this.store[key] || null; }),
    setItem: jest.fn(function(key, value) { this.store[key] = value; }),
    removeItem: jest.fn(function(key) { delete this.store[key]; }),
    clear: jest.fn(function() { this.store = {}; }),
  },
  writable: true
});

// Mock console
const originalConsole = console;
const mockConsole = { log: jest.fn(), error: jest.fn() };

describe('Session Storage Core Functions', () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.getItem.mockClear();
    localStorage.setItem.mockClear();
    localStorage.removeItem.mockClear();
    global.console = mockConsole;
    jest.clearAllMocks();
  });

  afterEach(() => {
    global.console = originalConsole;
  });

  test('storeSession stores data correctly', () => {
    storeSession('room123', 'Alice', 'session456', 'lobby');

    expect(localStorage.setItem).toHaveBeenCalledTimes(1);
    expect(localStorage.setItem).toHaveBeenCalledWith(
      'liap_tui_session',
      expect.stringContaining('room123')
    );
  });

  test('getSession retrieves stored data', () => {
    // Store data first
    const sessionData = {
      roomId: 'room123',
      playerName: 'Alice',
      sessionId: 'session456',
      createdAt: Date.now(),
      lastActivity: Date.now(),
      gamePhase: 'lobby',
    };

    localStorage.store['liap_tui_session'] = JSON.stringify(sessionData);

    const result = getSession();
    expect(result).toEqual(sessionData);
  });

  test('clearSession removes data', () => {
    // Store some data first
    localStorage.store['liap_tui_session'] = 'some data';

    clearSession();

    expect(localStorage.removeItem).toHaveBeenCalledWith('liap_tui_session');
  });

  test('hasValidSession returns correct boolean', () => {
    // No session initially
    expect(hasValidSession()).toBe(false);

    // Add valid session
    const sessionData = {
      roomId: 'room123',
      playerName: 'Alice',
      sessionId: 'session456',
      createdAt: Date.now(),
      lastActivity: Date.now(),
      gamePhase: 'lobby',
    };

    localStorage.store['liap_tui_session'] = JSON.stringify(sessionData);
    expect(hasValidSession()).toBe(true);

    // Clear session
    clearSession();
    expect(hasValidSession()).toBe(false);
  });

  test('handles localStorage errors gracefully', () => {
    localStorage.setItem.mockImplementationOnce(() => {
      throw new Error('Storage quota exceeded');
    });

    expect(() => {
      storeSession('room123', 'Alice', 'session456');
    }).not.toThrow();

    expect(mockConsole.error).toHaveBeenCalled();
  });
});