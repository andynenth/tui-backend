/**
 * Test Utilities for Service Testing
 *
 * Common utilities and helpers for testing GameService and NetworkService
 */

import MockWebSocket from '../../../__mocks__/websocket.js';

/**
 * Create a mock NetworkService for testing GameService in isolation
 */
export const createMockNetworkService = () => {
  const mockNetworkService = {
    connectToRoom: jest.fn(),
    disconnectFromRoom: jest.fn(),
    send: jest.fn(),
    getConnectionStatus: jest.fn(),
    getStatus: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    destroy: jest.fn(),

    // Test helpers
    mockEvents: new Map(),

    // Simulate events
    emit(eventType, detail) {
      const listeners = this.mockEvents.get(eventType) || [];
      listeners.forEach((listener) => {
        listener({ detail });
      });
    },

    // Override addEventListener to track listeners
    addEventListener: jest.fn((eventType, listener) => {
      if (!mockNetworkService.mockEvents.has(eventType)) {
        mockNetworkService.mockEvents.set(eventType, []);
      }
      mockNetworkService.mockEvents.get(eventType).push(listener);
    }),

    removeEventListener: jest.fn((eventType, listener) => {
      const listeners = mockNetworkService.mockEvents.get(eventType) || [];
      const index = listeners.indexOf(listener);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }),
  };

  // Default implementations
  mockNetworkService.connectToRoom.mockResolvedValue(
    new MockWebSocket('ws://test')
  );
  mockNetworkService.disconnectFromRoom.mockResolvedValue();
  mockNetworkService.send.mockReturnValue(true);
  mockNetworkService.getConnectionStatus.mockReturnValue({
    roomId: 'test-room',
    status: 'connected',
    connected: true,
    queueSize: 0,
    reconnecting: false,
  });
  mockNetworkService.getStatus.mockReturnValue({
    isDestroyed: false,
    activeConnections: 1,
    totalQueuedMessages: 0,
    rooms: {},
  });

  return mockNetworkService;
};

/**
 * Create test game state data
 */
export const createTestGameState = (overrides = {}) => ({
  roomId: null,
  playerName: null,
  isConnected: false,
  error: null,
  phase: 'waiting',
  currentRound: 1,
  players: [],
  myHand: [],
  roundStarter: null,
  weakHands: [],
  currentWeakPlayer: null,
  redealRequests: {},
  redealMultiplier: 1,
  declarations: {},
  declarationOrder: [],
  currentDeclarer: null,
  declarationTotal: 0,
  currentTurnStarter: null,
  turnOrder: [],
  currentPlayer: null,
  currentTurnPlays: [],
  requiredPieceCount: null,
  currentTurnNumber: 0,
  roundScores: {},
  totalScores: {},
  winners: [],
  disconnectedPlayers: [],
  host: null,
  isMyTurn: false,
  allowedActions: [],
  validOptions: [],
  lastEventSequence: 0,
  gameOver: false,
  gameStartTime: null,
  ...overrides,
});

/**
 * Create test phase data for different game phases
 */
export const createTestPhaseData = (phase, overrides = {}) => {
  const baseData = {
    phase,
    round: 1,
    players: [
      { name: 'Player1', score: 0, is_bot: false, is_host: false },
      { name: 'Player2', score: 0, is_bot: false, is_host: false },
      { name: 'Player3', score: 0, is_bot: false, is_host: false },
      { name: 'Player4', score: 0, is_bot: false, is_host: false },
    ],
  };

  switch (phase) {
    case 'preparation':
      return {
        ...baseData,
        my_hand: [
          { kind: 'GENERAL_RED', value: 15, color: 'red' },
          { kind: 'ADVISOR_RED', value: 12, color: 'red' },
          { kind: 'ELEPHANT_BLACK', value: 11, color: 'black' },
        ],
        weak_hands: [],
        current_weak_player: null,
        redeal_multiplier: 1,
        ...overrides,
      };

    case 'declaration':
      return {
        ...baseData,
        my_hand: [
          { kind: 'GENERAL_RED', value: 15, color: 'red' },
          { kind: 'ADVISOR_RED', value: 12, color: 'red' },
        ],
        declaration_order: ['Player1', 'Player2', 'Player3', 'Player4'],
        current_declarer: 'Player1',
        declarations: {},
        declaration_total: 0,
        ...overrides,
      };

    case 'turn':
      return {
        ...baseData,
        turn_order: ['Player1', 'Player2', 'Player3', 'Player4'],
        current_player: 'Player1',
        current_turn_starter: 'Player1',
        required_piece_count: 0,
        turn_plays: {},
        pile_counts: { Player1: 0, Player2: 0, Player3: 0, Player4: 0 },
        ...overrides,
      };

    case 'scoring':
      return {
        ...baseData,
        total_scores: { Player1: 10, Player2: 5, Player3: 8, Player4: 12 },
        round_scores: { Player1: 2, Player2: -1, Player3: 0, Player4: 3 },
        winners: ['Player4'],
        game_complete: false,
        ...overrides,
      };

    default:
      return { ...baseData, ...overrides };
  }
};

/**
 * Wait for next tick (useful for async operations)
 */
export const waitForNextTick = () =>
  new Promise((resolve) => setTimeout(resolve, 0));

/**
 * Wait for specific time
 */
export const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Create a mock event detail object
 */
export const createMockEventDetail = (eventType, data = {}, roomId = 'test-room') => ({
  detail: {
    roomId,
    data,
    timestamp: Date.now(),
    message: {
      event: eventType,
      data,
      sequence: 1,
      timestamp: Date.now(),
      id: 'test-id',
    },
  }
});

/**
 * Assert that a function throws with specific message
 */
export const expectToThrow = async (fn, expectedMessage) => {
  let error;
  try {
    await fn();
  } catch (e) {
    error = e;
  }

  if (!error) {
    throw new Error('Expected function to throw an error, but it did not');
  }
  
  if (expectedMessage) {
    expect(error.message).toContain(expectedMessage);
  }

  return error;
};

/**
 * Mock console methods to avoid noise in tests
 */
export const mockConsole = () => {
  const originalConsole = { ...console };

  beforeEach(() => {
    console.log = jest.fn();
    console.error = jest.fn();
    console.warn = jest.fn();
  });

  afterEach(() => {
    Object.assign(console, originalConsole);
  });
};
