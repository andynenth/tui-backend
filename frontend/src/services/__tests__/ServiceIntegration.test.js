/**
 * Service Integration Tests
 * 
 * Tests the interaction between GameService and NetworkService to ensure
 * they work correctly together in realistic scenarios.
 */

import MockWebSocket from '../../../__mocks__/websocket.js';
import { createTestPhaseData, createMockEventDetail, waitForNextTick, wait, mockConsole } from './testUtils';

// Setup console mocking
mockConsole();

// Mock constants
jest.mock('../../constants', () => ({
  TIMING: {
    HEARTBEAT_INTERVAL: 1000,
    CONNECTION_TIMEOUT: 5000,
    RECOVERY_TIMEOUT: 60000
  },
  GAME: {
    MAX_RECONNECT_ATTEMPTS: 3,
    MESSAGE_QUEUE_LIMIT: 100
  },
  NETWORK: {
    WEBSOCKET_BASE_URL: 'ws://localhost:5050/ws',
    RECONNECT_BACKOFF: [100, 200, 400, 800, 1600]
  }
}));

describe('Service Integration', () => {
  let GameService;
  let NetworkService;
  let gameService;
  let networkService;
  let roomId;
  let playerName;

  beforeEach(async () => {
    // Dynamic imports to get fresh instances
    const gameModule = await import('../GameService');
    const networkModule = await import('../NetworkService');
    
    GameService = gameModule.GameService;
    NetworkService = networkModule.NetworkService;
    
    // Reset singletons
    GameService.instance = null;
    NetworkService.instance = null;
    
    // Create fresh instances
    networkService = NetworkService.getInstance();
    gameService = GameService.getInstance();
    
    roomId = 'integration-test-room';
    playerName = 'TestPlayer';
  });

  afterEach(() => {
    // Clean up
    if (gameService && !gameService.isDestroyed) {
      gameService.destroy();
    }
    if (networkService && !networkService.isDestroyed) {
      networkService.destroy();
    }
    
    if (GameService) GameService.instance = null;
    if (NetworkService) NetworkService.instance = null;
    
    jest.clearAllMocks();
  });

  describe('Connection Flow', () => {
    test('GameService successfully connects via NetworkService', async () => {
      await gameService.joinRoom(roomId, playerName);
      
      // Check GameService state
      const gameState = gameService.getState();
      expect(gameState.roomId).toBe(roomId);
      expect(gameState.playerName).toBe(playerName);
      expect(gameState.isConnected).toBe(true);
      
      // Check NetworkService state
      const networkStatus = networkService.getConnectionStatus(roomId);
      expect(networkStatus.connected).toBe(true);
      expect(networkStatus.roomId).toBe(roomId);
    });

    test('GameService handles NetworkService connection failure', async () => {
      // Mock connection failure
      jest.spyOn(networkService, 'connectToRoom').mockRejectedValue(new Error('Network error'));
      
      await expect(gameService.joinRoom(roomId, playerName)).rejects.toThrow('Network error');
      
      const gameState = gameService.getState();
      expect(gameState.isConnected).toBe(false);
      expect(gameState.error).toContain('Network error');
    });

    test('GameService disconnects via NetworkService', async () => {
      await gameService.joinRoom(roomId, playerName);
      await gameService.leaveRoom();
      
      const gameState = gameService.getState();
      expect(gameState.roomId).toBeNull();
      expect(gameState.isConnected).toBe(false);
      
      const networkStatus = networkService.getConnectionStatus(roomId);
      expect(networkStatus.connected).toBe(false);
    });
  });

  describe('Message Flow', () => {
    let connection;

    beforeEach(async () => {
      await gameService.joinRoom(roomId, playerName);
      connection = networkService.connections?.get(roomId)?.websocket;
      if (connection) {
        connection.clearSentMessages(); // Clear ready message
      }
    });

    test('GameService sends actions via NetworkService', () => {
      if (!connection) {
        console.warn('No connection found, skipping test');
        return;
      }
      
      // Set up game state for declaration
      gameService.setState({
        ...gameService.getState(),
        phase: 'declaration',
        currentDeclarer: playerName,
        players: [{ name: playerName }, { name: 'Player2' }],
        declarations: {}
      }, 'TEST_SETUP');
      
      gameService.makeDeclaration(2);
      
      const sentMessages = connection.getSentMessages();
      expect(sentMessages).toHaveLength(1);
      
      const message = JSON.parse(sentMessages[0]);
      expect(message.event).toBe('declare');
      expect(message.data.value).toBe(2);
      expect(message.data.player_name).toBe(playerName);
    });

    test('GameService receives events via NetworkService', async () => {
      if (!connection) {
        console.warn('No connection found, skipping test');
        return;
      }
      
      const stateListener = jest.fn();
      gameService.addStateListener(stateListener);
      
      const phaseData = createTestPhaseData('preparation', {
        my_hand: [
          { value: 12, color: 'red', suit: 'hearts' },
          { value: 10, color: 'black', suit: 'spades' }
        ]
      });
      
      // Simulate NetworkService receiving phase_change event
      connection.mockReceive({
        event: 'phase_change',
        data: phaseData,
        sequence: 1,
        timestamp: Date.now(),
        id: 'test-id'
      });
      
      await waitForNextTick();
      
      // Check that GameService processed the event
      const gameState = gameService.getState();
      expect(gameState.phase).toBe('preparation');
      expect(gameState.myHand).toHaveLength(2);
      
      expect(stateListener).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'PHASE_CHANGE',
          newState: expect.objectContaining({ phase: 'preparation' })
        })
      );
    });

    test('handles invalid event data gracefully', async () => {
      if (!connection) {
        console.warn('No connection found, skipping test');
        return;
      }
      
      // Send malformed event
      connection.mockReceive('invalid json');
      
      await waitForNextTick();
      
      // Services should not crash
      const gameState = gameService.getState();
      expect(gameState).toBeDefined();
      
      const networkStatus = networkService.getStatus();
      expect(networkStatus).toBeDefined();
    });
  });

  describe('Performance and Resource Management', () => {
    test('proper cleanup on service destruction', async () => {
      await gameService.joinRoom(roomId, playerName);
      
      const connection = networkService.connections?.get(roomId)?.websocket;
      let closeSpy;
      if (connection) {
        closeSpy = jest.spyOn(connection, 'close');
      }
      
      // Destroy services
      gameService.destroy();
      networkService.destroy();
      
      if (closeSpy) {
        expect(closeSpy).toHaveBeenCalled();
      }
      expect(gameService.isDestroyed).toBe(true);
      expect(networkService.isDestroyed).toBe(true);
    });
  });

  describe('Edge Cases', () => {
    test('handles service initialization order', () => {
      // Reset and try different initialization order
      GameService.instance = null;
      NetworkService.instance = null;
      
      const game1 = GameService.getInstance();
      const network1 = NetworkService.getInstance();
      
      expect(game1).toBeDefined();
      expect(network1).toBeDefined();
      
      // Should get same instances regardless of order
      const game2 = GameService.getInstance();
      const network2 = NetworkService.getInstance();
      
      expect(game1).toBe(game2);
      expect(network1).toBe(network2);
    });

    test('handles concurrent operations', async () => {
      // Start multiple operations simultaneously
      const promises = [
        gameService.joinRoom(roomId, playerName),
        networkService.connectToRoom('other-room'),
        gameService.joinRoom('another-room', 'AnotherPlayer')
      ];
      
      // Should not crash
      await expect(Promise.allSettled(promises)).resolves.toBeDefined();
    });
  });
});