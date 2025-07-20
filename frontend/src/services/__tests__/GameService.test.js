/**
 * GameService Tests
 *
 * Comprehensive test suite for GameService including singleton pattern,
 * room management, game actions, event handling, and state management.
 */

import {
  createMockNetworkService,
  createTestGameState,
  createTestPhaseData,
  createMockEventDetail,
  expectToThrow,
  waitForNextTick,
  mockConsole,
} from './testUtils';

import MockWebSocket from '../../../__mocks__/websocket.js';

// Setup console mocking
mockConsole();

// Mock the NetworkService import
jest.mock('../NetworkService', () => ({
  networkService: null, // Will be replaced with mock in each test
}));

describe('GameService', () => {
  let mockNetworkService;
  let GameService;
  let gameService;

  beforeEach(async () => {
    // Dynamic import to get fresh instance
    const module = await import('../GameService');
    GameService = module.GameService;

    // Reset singleton
    GameService.instance = null;

    // Create fresh mock network service
    mockNetworkService = createMockNetworkService();

    // Mock the networkService import
    const NetworkServiceModule = require('../NetworkService');
    NetworkServiceModule.networkService = mockNetworkService;

    // Get fresh GameService instance
    gameService = GameService.getInstance();
  });

  afterEach(() => {
    // Clean up
    if (gameService && !gameService.isDestroyed) {
      gameService.destroy();
    }
    if (GameService) {
      GameService.instance = null;
    }
    jest.clearAllMocks();
  });

  describe('Singleton Pattern', () => {
    test('getInstance returns same instance', () => {
      const instance1 = GameService.getInstance();
      const instance2 = GameService.getInstance();

      expect(instance1).toBe(instance2);
    });

    test('constructor throws when called directly', () => {
      expect(() => new GameService()).toThrow('GameService is a singleton');
    });

    test('multiple getInstance calls return same instance', () => {
      const instances = Array.from({ length: 5 }, () =>
        GameService.getInstance()
      );

      instances.forEach((instance) => {
        expect(instance).toBe(gameService);
      });
    });
  });

  describe('Initial State', () => {
    test('has correct initial state', () => {
      const state = gameService.getState();

      expect(state).toMatchObject({
        roomId: null,
        playerName: '',
        isConnected: false,
        isConnecting: false,
        error: null,
        phase: 'lobby',
      });
    });

    test('getState returns immutable object', () => {
      const state1 = gameService.getState();
      const state2 = gameService.getState();

      expect(state1).not.toBe(state2); // Different objects
      expect(state1).toEqual(state2); // Same content
    });
  });

  describe('Room Management', () => {
    describe('joinRoom', () => {
      test('successfully joins room', async () => {
        const roomId = 'test-room';
        const playerName = 'TestPlayer';

        await gameService.joinRoom(roomId, playerName);

        expect(mockNetworkService.connectToRoom).toHaveBeenCalledWith(roomId);

        const state = gameService.getState();
        expect(state.roomId).toBe(roomId);
        expect(state.playerName).toBe(playerName);
        expect(state.isConnected).toBe(true);
        expect(state.error).toBeNull();
      });

      test('handles connection failure', async () => {
        const roomId = 'test-room';
        const playerName = 'TestPlayer';
        const errorMessage = 'Connection failed';

        mockNetworkService.connectToRoom.mockRejectedValue(
          new Error(errorMessage)
        );

        await expectToThrow(
          () => gameService.joinRoom(roomId, playerName),
          errorMessage
        );

        const state = gameService.getState();
        expect(state.error).toContain(errorMessage);
        expect(state.isConnected).toBe(false);
      });

      test('rejects when service is destroyed', async () => {
        gameService.destroy();

        await expectToThrow(
          () => gameService.joinRoom('room', 'player'),
          'GameService has been destroyed'
        );
      });
    });

    describe('leaveRoom', () => {
      test('successfully leaves room', async () => {
        // First join a room
        await gameService.joinRoom('test-room', 'TestPlayer');

        // Then leave
        await gameService.leaveRoom();

        expect(mockNetworkService.disconnectFromRoom).toHaveBeenCalledWith(
          'test-room'
        );

        const state = gameService.getState();
        expect(state.roomId).toBeNull();
        expect(state.isConnected).toBe(false);
        expect(state.playerName).toBe('TestPlayer'); // Preserved
      });

      test('does nothing when not in room', async () => {
        await gameService.leaveRoom();

        expect(mockNetworkService.disconnectFromRoom).not.toHaveBeenCalled();
      });
    });
  });

  describe('Game Actions', () => {
    beforeEach(async () => {
      // Join room and set up for game actions
      await gameService.joinRoom('test-room', 'TestPlayer');
    });

    describe('Redeal Actions', () => {
      test('acceptRedeal sends correct action', () => {
        // Set preparation phase
        gameService.setState(
          {
            ...gameService.getState(),
            phase: 'preparation',
          },
          'TEST_SETUP'
        );

        gameService.acceptRedeal();

        expect(mockNetworkService.send).toHaveBeenCalledWith(
          'test-room',
          'accept_redeal',
          { player_name: 'TestPlayer' }
        );
      });

      test('declineRedeal sends correct action', () => {
        gameService.setState(
          {
            ...gameService.getState(),
            phase: 'preparation',
          },
          'TEST_SETUP'
        );

        gameService.declineRedeal();

        expect(mockNetworkService.send).toHaveBeenCalledWith(
          'test-room',
          'decline_redeal',
          { player_name: 'TestPlayer' }
        );
      });

      test('redeal actions fail in wrong phase', () => {
        gameService.setState(
          {
            ...gameService.getState(),
            phase: 'turn',
          },
          'TEST_SETUP'
        );

        expect(() => gameService.acceptRedeal()).toThrow(
          'Invalid action ACCEPT_REDEAL for phase turn'
        );
        expect(() => gameService.declineRedeal()).toThrow(
          'Invalid action DECLINE_REDEAL for phase turn'
        );
      });
    });

    describe('Declaration', () => {
      beforeEach(() => {
        // Set declaration phase with test player as current declarer
        gameService.setState(
          {
            ...gameService.getState(),
            phase: 'declaration',
            currentDeclarer: 'TestPlayer',
            players: [
              { name: 'TestPlayer' },
              { name: 'Player2' },
              { name: 'Player3' },
              { name: 'Player4' },
            ],
            declarations: {},
          },
          'TEST_SETUP'
        );
      });

      test('makeDeclaration with valid value', () => {
        gameService.makeDeclaration(2);

        expect(mockNetworkService.send).toHaveBeenCalledWith(
          'test-room',
          'declare',
          { value: 2, player_name: 'TestPlayer' }
        );
      });

      test('makeDeclaration validates value range', () => {
        expect(() => gameService.makeDeclaration(-1)).toThrow(
          'Invalid declaration value: -1'
        );
        expect(() => gameService.makeDeclaration(9)).toThrow(
          'Invalid declaration value: 9'
        );
        expect(() => gameService.makeDeclaration('invalid')).toThrow(
          'Invalid declaration value: invalid'
        );
      });

      test('makeDeclaration fails when not player turn', () => {
        gameService.setState(
          {
            ...gameService.getState(),
            currentDeclarer: 'OtherPlayer',
          },
          'TEST_SETUP'
        );

        expect(() => gameService.makeDeclaration(2)).toThrow(
          'Not your turn to declare'
        );
      });

      test('last player cannot make total equal 8', () => {
        // Set up as last player with existing declarations totaling 6
        gameService.setState(
          {
            ...gameService.getState(),
            declarations: { Player2: 2, Player3: 2, Player4: 2 }, // Total = 6
          },
          'TEST_SETUP'
        );

        expect(() => gameService.makeDeclaration(2)).toThrow(
          'Last player cannot make total equal 8'
        );
      });
    });

    describe('Play Pieces', () => {
      beforeEach(() => {
        // Set turn phase with test player as current player
        gameService.setState(
          {
            ...gameService.getState(),
            phase: 'turn',
            currentPlayer: 'TestPlayer',
            myHand: [
              { value: 12, color: 'red', suit: 'hearts' },
              { value: 11, color: 'red', suit: 'diamonds' },
              { value: 10, color: 'black', suit: 'spades' },
            ],
          },
          'TEST_SETUP'
        );
      });

      test('playPieces with valid indices', () => {
        gameService.playPieces([0, 1]);

        expect(mockNetworkService.send).toHaveBeenCalledWith(
          'test-room',
          'play_pieces',
          expect.objectContaining({
            piece_indexes: [0, 1],
            player_name: 'TestPlayer',
          })
        );
      });

      test('playPieces validates indices array', () => {
        expect(() => gameService.playPieces([])).toThrow(
          'Must select at least one piece'
        );
        expect(() => gameService.playPieces('invalid')).toThrow(
          'Must select at least one piece'
        );
        expect(() => gameService.playPieces(null)).toThrow(
          'Must select at least one piece'
        );
      });

      test('playPieces validates not player turn', () => {
        gameService.setState(
          {
            ...gameService.getState(),
            currentPlayer: 'OtherPlayer',
          },
          'TEST_SETUP'
        );

        expect(() => gameService.playPieces([0])).toThrow(
          'Not your turn to play'
        );
      });

      test('playPieces validates piece indices', () => {
        expect(() => gameService.playPieces([-1])).toThrow(
          'Invalid piece index: -1'
        );
        expect(() => gameService.playPieces([3])).toThrow(
          'Invalid piece index: 3'
        );
        expect(() => gameService.playPieces([0, 1, 5])).toThrow(
          'Invalid piece index: 5'
        );
      });

      test('playPieces fails in wrong phase', () => {
        gameService.setState(
          {
            ...gameService.getState(),
            phase: 'declaration',
          },
          'TEST_SETUP'
        );

        expect(() => gameService.playPieces([0])).toThrow(
          'Invalid action PLAY_PIECES for phase declaration'
        );
      });
    });
  });

  describe('Event Handling', () => {
    beforeEach(async () => {
      await gameService.joinRoom('test-room', 'TestPlayer');
    });

    test('processes phase_change events', async () => {
      const phaseData = createTestPhaseData('declaration', {
        current_declarer: 'TestPlayer',
      });

      // Simulate phase_change event
      const eventDetail = createMockEventDetail('phase_change', phaseData);
      mockNetworkService.emit('phase_change', eventDetail);

      await waitForNextTick();

      const state = gameService.getState();
      expect(state.phase).toBe('declaration');
      expect(state.currentDeclarer).toBe('TestPlayer');
    });

    test('processes error events', async () => {
      const errorMessage = 'Test error';
      const eventDetail = createMockEventDetail('error', {
        message: errorMessage,
      });

      mockNetworkService.emit('error', eventDetail);

      await waitForNextTick();

      const state = gameService.getState();
      expect(state.error).toBe(errorMessage);
    });

    test('emits state changes to listeners', async () => {
      const listener = jest.fn();
      gameService.addStateListener(listener);

      const phaseData = createTestPhaseData('turn');
      const eventDetail = createMockEventDetail('phase_change', phaseData);

      mockNetworkService.emit('phase_change', eventDetail);

      await waitForNextTick();

      expect(listener).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'PHASE_CHANGE',
          newState: expect.objectContaining({ phase: 'turn' }),
        })
      );
    });
  });

  describe('Service Lifecycle', () => {
    test('destroy cleans up resources', async () => {
      await gameService.joinRoom('test-room', 'TestPlayer');

      gameService.destroy();

      expect(mockNetworkService.disconnectFromRoom).toHaveBeenCalledWith(
        'test-room'
      );
      expect(gameService.isDestroyed).toBe(true);
    });

    test('operations fail after destroy', async () => {
      gameService.destroy();

      await expectToThrow(
        () => gameService.joinRoom('room', 'player'),
        'GameService has been destroyed'
      );

      expect(() => gameService.getState()).toThrow(
        'GameService has been destroyed'
      );
    });
  });

  describe('Player Name Integration', () => {
    test('joinRoom calls NetworkService.connectToRoom with playerName', async () => {
      const roomId = 'test-room';
      const playerName = 'TestPlayer';

      // Mock successful connection
      mockNetworkService.connectToRoom.mockResolvedValue(new MockWebSocket());

      await gameService.joinRoom(roomId, playerName);

      // Verify NetworkService was called with playerName
      expect(mockNetworkService.connectToRoom).toHaveBeenCalledWith(
        roomId,
        { playerName }
      );
    });

    test('joinRoom handles connection errors gracefully', async () => {
      const roomId = 'test-room';
      const playerName = 'TestPlayer';
      const errorMessage = 'Connection failed';

      // Mock connection failure
      mockNetworkService.connectToRoom.mockRejectedValue(
        new Error(errorMessage)
      );

      await expectToThrow(
        () => gameService.joinRoom(roomId, playerName),
        errorMessage
      );

      // Verify state was updated with error
      const state = gameService.getState();
      expect(state.error).toContain(errorMessage);
      expect(state.isConnected).toBe(false);
    });

    test('player name is stored in GameService state', async () => {
      const roomId = 'test-room';
      const playerName = 'Alice';

      // Mock successful connection
      mockNetworkService.connectToRoom.mockResolvedValue(new MockWebSocket());

      await gameService.joinRoom(roomId, playerName);

      // Verify player name is stored in state
      const state = gameService.getState();
      expect(state.playerName).toBe(playerName);
      expect(state.roomId).toBe(roomId);
      expect(state.isConnected).toBe(true);
    });

    test('player name persists across state updates', async () => {
      const roomId = 'test-room';
      const playerName = 'Bob';

      // Join room
      mockNetworkService.connectToRoom.mockResolvedValue(new MockWebSocket());
      await gameService.joinRoom(roomId, playerName);

      // Simulate phase change event
      const phaseData = createTestPhaseData({
        phase: 'preparation',
        players: [
          { name: playerName, score: 0, is_bot: false },
          { name: 'Charlie', score: 0, is_bot: false }
        ]
      });

      gameService.handleNetworkEvent(
        createMockEventDetail('phase_change', roomId, phaseData)
      );

      // Verify player name is still in state
      const state = gameService.getState();
      expect(state.playerName).toBe(playerName);
      expect(state.phase).toBe('preparation');
    });

    test('leaveRoom preserves player name', async () => {
      const roomId = 'test-room';
      const playerName = 'Charlie';

      // Join and then leave room
      mockNetworkService.connectToRoom.mockResolvedValue(new MockWebSocket());
      await gameService.joinRoom(roomId, playerName);
      await gameService.leaveRoom();

      // Verify player name is preserved after leaving
      const state = gameService.getState();
      expect(state.playerName).toBe(playerName); // Should be preserved
      expect(state.roomId).toBeNull(); // Should be cleared
      expect(state.isConnected).toBe(false);
    });
  });
});
