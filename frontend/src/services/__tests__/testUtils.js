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
      listeners.forEach(listener => {
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
    })
  };
  
  // Default implementations
  mockNetworkService.connectToRoom.mockResolvedValue(new MockWebSocket('ws://test'));
  mockNetworkService.disconnectFromRoom.mockResolvedValue();
  mockNetworkService.send.mockReturnValue(true);
  mockNetworkService.getConnectionStatus.mockReturnValue({
    roomId: 'test-room',
    status: 'connected',
    connected: true,
    queueSize: 0,
    reconnecting: false
  });
  mockNetworkService.getStatus.mockReturnValue({
    isDestroyed: false,
    activeConnections: 1,
    totalQueuedMessages: 0,
    rooms: {}
  });
  
  return mockNetworkService;
};

/**
 * Create test game state data
 */
export const createTestGameState = (overrides = {}) => ({
  roomId: null,
  playerName: '',
  isConnected: false,
  isConnecting: false,
  error: null,
  phase: 'lobby',
  players: [],
  myHand: [],
  currentPlayer: '',
  declarations: {},
  ...overrides
});

/**
 * Create test phase data for different game phases
 */
export const createTestPhaseData = (phase, overrides = {}) => {
  const baseData = {
    phase,
    players: [
      { name: 'Player1', id: 'p1' },
      { name: 'Player2', id: 'p2' },
      { name: 'Player3', id: 'p3' },
      { name: 'Player4', id: 'p4' }
    ]
  };
  
  switch (phase) {
    case 'preparation':
      return {
        ...baseData,
        my_hand: [
          { value: 12, color: 'red', suit: 'hearts' },
          { value: 11, color: 'red', suit: 'diamonds' },
          { value: 10, color: 'black', suit: 'spades' }
        ],
        weak_hand_players: [],
        redeal_responses: {},
        ...overrides
      };
      
    case 'declaration':
      return {
        ...baseData,
        my_hand: [
          { value: 12, color: 'red', suit: 'hearts' },
          { value: 11, color: 'red', suit: 'diamonds' }
        ],
        declaration_order: ['Player1', 'Player2', 'Player3', 'Player4'],
        current_declarer: 'Player1',
        declarations: {},
        declaration_total: 0,
        ...overrides
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
        ...overrides
      };
      
    case 'scoring':
      return {
        ...baseData,
        scores: { Player1: 10, Player2: 5, Player3: 8, Player4: 12 },
        round_scores: { Player1: 2, Player2: -1, Player3: 0, Player4: 3 },
        winner: 'Player4',
        ...overrides
      };
      
    default:
      return { ...baseData, ...overrides };
  }
};

/**
 * Wait for next tick (useful for async operations)
 */
export const waitForNextTick = () => new Promise(resolve => setTimeout(resolve, 0));

/**
 * Wait for specific time
 */
export const wait = (ms) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Create a mock event detail object
 */
export const createMockEventDetail = (eventType, data = {}) => ({
  roomId: 'test-room',
  data,
  timestamp: Date.now(),
  message: {
    event: eventType,
    data,
    sequence: 1,
    timestamp: Date.now(),
    id: 'test-id'
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
  
  expect(error).toBeDefined();
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