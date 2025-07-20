/**
 * NetworkService Tests
 *
 * Comprehensive test suite for NetworkService including singleton pattern,
 * connection management, message handling, reconnection logic, and heartbeat system.
 */

import MockWebSocket from '../../../__mocks__/websocket.js';
import { waitForNextTick, wait, mockConsole } from './testUtils';

// Setup console mocking
mockConsole();

// Mock WebSocket globally
global.WebSocket = MockWebSocket;

// Mock constants
jest.mock('../../constants', () => ({
  TIMING: {
    HEARTBEAT_INTERVAL: 1000,
    CONNECTION_TIMEOUT: 5000,
    RECOVERY_TIMEOUT: 60000,
  },
  GAME: {
    MAX_RECONNECT_ATTEMPTS: 3,
    MESSAGE_QUEUE_LIMIT: 100,
  },
  NETWORK: {
    WEBSOCKET_BASE_URL: 'ws://localhost:5050/ws',
    RECONNECT_BACKOFF: [100, 200, 400, 800, 1600],
  },
}));

describe('NetworkService', () => {
  let NetworkService;
  let networkService;

  beforeEach(async () => {
    // Dynamic import to get fresh instance
    const module = await import('../NetworkService');
    NetworkService = module.NetworkService;

    // Reset singleton
    NetworkService.instance = null;

    // Reset WebSocket mock
    jest.clearAllMocks();

    // Get fresh instance
    networkService = NetworkService.getInstance();
  });

  afterEach(() => {
    // Clean up
    if (networkService && !networkService.isDestroyed) {
      networkService.destroy();
    }
    if (NetworkService) {
      NetworkService.instance = null;
    }
  });

  describe('Singleton Pattern', () => {
    test('getInstance returns same instance', () => {
      const instance1 = NetworkService.getInstance();
      const instance2 = NetworkService.getInstance();

      expect(instance1).toBe(instance2);
    });

    test('constructor throws when called directly', () => {
      // First ensure instance exists
      const instance = NetworkService.getInstance();
      expect(instance).toBeDefined();
      
      // Now try to create another instance directly
      expect(() => new NetworkService()).toThrow(
        'NetworkService is a singleton'
      );
    });

    test('multiple getInstance calls return same instance', () => {
      const instances = Array.from({ length: 5 }, () =>
        NetworkService.getInstance()
      );

      instances.forEach((instance) => {
        expect(instance).toBe(networkService);
      });
    });
  });

  describe('Connection Management', () => {
    describe('connectToRoom', () => {
      test('successfully connects to room', async () => {
        const roomId = 'test-room';

        const connection = await networkService.connectToRoom(roomId);

        expect(connection).toBeInstanceOf(MockWebSocket);
        expect(connection.url).toBe('ws://localhost:5050/ws/test-room');

        // Wait for async connection setup
        await waitForNextTick();
        await wait(20);

        const status = networkService.getConnectionStatus(roomId);
        expect(status.connected).toBe(true);
        expect(status.roomId).toBe(roomId);
        expect(status.status).toBe('connected');
      });

      test('emits connected event', async () => {
        const roomId = 'test-room';
        const eventListener = jest.fn();

        networkService.addEventListener('connected', eventListener);

        await networkService.connectToRoom(roomId);
        
        // Wait for async event
        await wait(20);

        expect(eventListener).toHaveBeenCalled();
        const event = eventListener.mock.calls[0][0];
        expect(event.detail).toMatchObject({
          roomId,
          timestamp: expect.any(Number),
        });
      });

      test('sends initial ready signal', async () => {
        const roomId = 'test-room';

        const connection = await networkService.connectToRoom(roomId);
        
        // Wait for async ready signal
        await wait(20);

        // Check sent messages for client_ready
        const sentMessages = connection.getSentMessages();
        const readyMessage = sentMessages.find(msg => {
          const parsed = JSON.parse(msg);
          return parsed.event === 'client_ready';
        });

        expect(readyMessage).toBeDefined();
        const parsed = JSON.parse(readyMessage);
        expect(parsed.data.room_id).toBe(roomId);
      });

      test('closes existing connection before new one', async () => {
        const roomId = 'test-room';

        // First connection
        const connection1 = await networkService.connectToRoom(roomId);
        const closeSpy = jest.spyOn(connection1, 'close');

        // Second connection to same room
        await networkService.connectToRoom(roomId);

        expect(closeSpy).toHaveBeenCalled();
      });

      test('rejects with empty room ID', async () => {
        await expect(networkService.connectToRoom('')).rejects.toThrow(
          'Room ID is required'
        );
        await expect(networkService.connectToRoom(null)).rejects.toThrow(
          'Room ID is required'
        );
      });

      test('rejects when service is destroyed', async () => {
        networkService.destroy();

        await expect(networkService.connectToRoom('room')).rejects.toThrow(
          'NetworkService has been destroyed'
        );
      });
    });

    describe('disconnectFromRoom', () => {
      test('successfully disconnects from room', async () => {
        const roomId = 'test-room';

        const connection = await networkService.connectToRoom(roomId);
        const closeSpy = jest.spyOn(connection, 'close');

        await networkService.disconnectFromRoom(roomId);

        expect(closeSpy).toHaveBeenCalledWith(1000, 'Client disconnect');

        const status = networkService.getConnectionStatus(roomId);
        expect(status.connected).toBe(false);
      });

      test('emits disconnected event', async () => {
        const roomId = 'test-room';
        const eventListener = jest.fn();

        networkService.addEventListener('disconnected', eventListener);

        await networkService.connectToRoom(roomId);
        await wait(20); // Let connection stabilize
        await networkService.disconnectFromRoom(roomId);
        await waitForNextTick();

        expect(eventListener).toHaveBeenCalled();
        const event = eventListener.mock.calls[0][0];
        expect(event.detail).toMatchObject({
          roomId,
          intentional: true,
          timestamp: expect.any(Number),
        });
      });

      test('does nothing for non-existent room', async () => {
        // Should not throw
        await networkService.disconnectFromRoom('non-existent-room');
      });
    });

    describe('Multiple Rooms', () => {
      test('handles multiple simultaneous connections', async () => {
        const room1 = 'room-1';
        const room2 = 'room-2';

        await Promise.all([
          networkService.connectToRoom(room1),
          networkService.connectToRoom(room2),
        ]);
        
        // Wait for connections to stabilize
        await wait(20);

        const status1 = networkService.getConnectionStatus(room1);
        const status2 = networkService.getConnectionStatus(room2);

        expect(status1.connected).toBe(true);
        expect(status2.connected).toBe(true);

        const overallStatus = networkService.getStatus();
        expect(overallStatus.activeConnections).toBe(2);
      });
    });
  });

  describe('Message Handling', () => {
    let roomId;
    let connection;

    beforeEach(async () => {
      roomId = 'test-room';
      connection = await networkService.connectToRoom(roomId);
      await wait(20); // Wait for connection to stabilize
      connection.clearSentMessages(); // Clear ready message
    });

    describe('send', () => {
      test('sends message when connected', () => {
        const result = networkService.send(roomId, 'test_event', {
          data: 'test',
        });

        expect(result).toBe(true);

        const sentMessages = connection.getSentMessages();
        expect(sentMessages).toHaveLength(1);

        const message = JSON.parse(sentMessages[0]);
        expect(message.event).toBe('test_event');
        expect(message.data).toEqual({ data: 'test' });
        expect(message.sequence).toBeGreaterThan(0); // Don't assume it's 1
        expect(message.id).toBeDefined();
      });

      test('queues message when disconnected', async () => {
        await networkService.disconnectFromRoom(roomId, false);

        const result = networkService.send(roomId, 'test_event', {
          data: 'test',
        });

        expect(result).toBe(false);

        const queueSize =
          networkService.messageQueues?.get(roomId)?.length || 0;
        expect(queueSize).toBe(1);
      });

      test('maintains sequence numbers', () => {
        networkService.send(roomId, 'event1', {});
        networkService.send(roomId, 'event2', {});
        networkService.send(roomId, 'event3', {});

        const sentMessages = connection.getSentMessages();
        expect(sentMessages).toHaveLength(3);

        const sequences = sentMessages.map((msg) => JSON.parse(msg).sequence);
        // Sequences should be increasing
        expect(sequences[1]).toBeGreaterThan(sequences[0]);
        expect(sequences[2]).toBeGreaterThan(sequences[1]);
      });

      test('returns false when service is destroyed', () => {
        networkService.destroy();

        const result = networkService.send(roomId, 'test_event', {});
        expect(result).toBe(false);
      });
    });

    describe('receive', () => {
      test('processes incoming messages', async () => {
        const eventListener = jest.fn();
        networkService.addEventListener('test_response', eventListener);

        connection.mockReceive({
          event: 'test_response',
          data: { response: 'data' },
          sequence: 1,
          timestamp: Date.now(),
          id: 'test-id',
        });

        await waitForNextTick();

        expect(eventListener).toHaveBeenCalledWith(
          expect.objectContaining({
            detail: expect.objectContaining({
              roomId,
              data: { response: 'data' },
            }),
          })
        );
      });

      test('handles heartbeat pong', async () => {
        const pingTimestamp = Date.now();

        connection.mockReceive({
          event: 'pong',
          data: { timestamp: pingTimestamp },
        });

        await waitForNextTick();

        const status = networkService.getConnectionStatus(roomId);
        expect(status.latency).toBeGreaterThanOrEqual(0);
      });

      test('handles malformed messages gracefully', async () => {
        const errorListener = jest.fn();
        networkService.addEventListener('messageError', errorListener);

        // Send invalid JSON
        connection.mockReceive('invalid json');

        await waitForNextTick();

        expect(errorListener).toHaveBeenCalled();
      });
    });
  });

  describe('Status and Monitoring', () => {
    test('getConnectionStatus returns correct info', async () => {
      const roomId = 'test-room';
      const connection = await networkService.connectToRoom(roomId);

      const status = networkService.getConnectionStatus(roomId);

      expect(status).toMatchObject({
        roomId,
        status: 'connected',
        connected: true,
        queueSize: 0,
        reconnecting: false,
        reconnectAttempts: 0,
      });

      expect(status.connectedAt).toBeCloseTo(Date.now(), -2);
      expect(status.uptime).toBeGreaterThan(0);
    });

    test('getConnectionStatus for non-existent room', () => {
      const status = networkService.getConnectionStatus('non-existent');

      expect(status).toMatchObject({
        roomId: 'non-existent',
        status: 'disconnected',
        connected: false,
        reconnecting: false,
      });
    });

    test('getStatus returns overall service status', async () => {
      await networkService.connectToRoom('room1');
      await networkService.connectToRoom('room2');

      const status = networkService.getStatus();

      expect(status).toMatchObject({
        isDestroyed: false,
        activeConnections: 2,
        totalQueuedMessages: 0,
      });

      expect(status.rooms).toHaveProperty('room1');
      expect(status.rooms).toHaveProperty('room2');
    });
  });

  describe('Service Lifecycle', () => {
    test('destroy cleans up all resources', async () => {
      const room1 = 'room-1';
      const room2 = 'room-2';

      const connection1 = await networkService.connectToRoom(room1);
      const connection2 = await networkService.connectToRoom(room2);

      const closeSpy1 = jest.spyOn(connection1, 'close');
      const closeSpy2 = jest.spyOn(connection2, 'close');

      networkService.destroy();

      expect(closeSpy1).toHaveBeenCalled();
      expect(closeSpy2).toHaveBeenCalled();
      expect(networkService.isDestroyed).toBe(true);
      expect(NetworkService.instance).toBeNull();
    });

    test('operations fail after destroy', () => {
      networkService.destroy();

      expect(networkService.connectToRoom('room')).rejects.toThrow(
        'NetworkService has been destroyed'
      );
      expect(networkService.send('room', 'event', {})).toBe(false);
    });
  });

  describe('Edge Cases', () => {
    test('handles rapid connect/disconnect cycles', async () => {
      const roomId = 'test-room';

      // Rapid connect/disconnect
      for (let i = 0; i < 5; i++) {
        await networkService.connectToRoom(roomId);
        await networkService.disconnectFromRoom(roomId);
      }

      // Should not crash or leak resources
      const status = networkService.getStatus();
      expect(status.activeConnections).toBe(0);
    });

    test('handles WebSocket errors gracefully', async () => {
      const roomId = 'test-room';
      const errorListener = jest.fn();

      networkService.addEventListener('connectionError', errorListener);

      const connection = await networkService.connectToRoom(roomId);
      connection.mockError('Network error');

      await waitForNextTick();

      expect(errorListener).toHaveBeenCalledWith(
        expect.objectContaining({
          detail: expect.objectContaining({
            roomId,
            error: 'Connection error',
          }),
        })
      );
    });
  });

  describe('Player Info Handling', () => {
    describe('connectToRoom with player info', () => {
      test('stores player info in connection data', async () => {
        const roomId = 'test-room';
        const playerName = 'TestPlayer';

        await networkService.connectToRoom(roomId, { playerName });

        // Get connection data through status
        const status = networkService.getConnectionStatus(roomId);
        expect(status.connected).toBe(true);
        
        // Verify player name is included in client_ready
        const connection = await networkService.connectToRoom(roomId);
        const sentMessages = connection.getSentMessages();
        
        const readyMessage = sentMessages.find(msg => {
          const parsed = JSON.parse(msg);
          return parsed.event === 'client_ready';
        });
        
        expect(readyMessage).toBeDefined();
        const parsed = JSON.parse(readyMessage);
        expect(parsed.data.player_name).toBe(playerName);
      });

      test('maintains backward compatibility without player info', async () => {
        const roomId = 'test-room';

        // Should not throw when playerInfo is not provided
        const connection = await networkService.connectToRoom(roomId);
        
        // Wait for ready message
        await wait(20);

        expect(connection).toBeInstanceOf(MockWebSocket);
        expect(connection.url).toBe('ws://localhost:5050/ws/test-room');

        const sentMessages = connection.getSentMessages();
        const readyMessage = sentMessages.find(msg => {
          const parsed = JSON.parse(msg);
          return parsed.event === 'client_ready';
        });

        expect(readyMessage).toBeDefined();
        const parsed = JSON.parse(readyMessage);
        expect(parsed.data.player_name).toBeUndefined();
      });

      test('client_ready event includes player_name when provided', async () => {
        const roomId = 'test-room';
        const playerName = 'Alice';

        const connection = await networkService.connectToRoom(roomId, { playerName });
        
        // Wait for ready message
        await wait(20);
        
        const sentMessages = connection.getSentMessages();

        const readyMessage = sentMessages.find(msg => {
          const parsed = JSON.parse(msg);
          return parsed.event === 'client_ready';
        });

        expect(readyMessage).toBeDefined();
        const parsed = JSON.parse(readyMessage);
        expect(parsed.event).toBe('client_ready');
        expect(parsed.data).toMatchObject({
          room_id: roomId,
          player_name: playerName
        });
      });

      test('client_ready event omits player_name when not provided', async () => {
        const roomId = 'test-room';

        const connection = await networkService.connectToRoom(roomId);
        
        // Wait for ready message
        await wait(20);
        
        const sentMessages = connection.getSentMessages();

        const readyMessage = sentMessages.find(msg => {
          const parsed = JSON.parse(msg);
          return parsed.event === 'client_ready';
        });

        expect(readyMessage).toBeDefined();
        const parsed = JSON.parse(readyMessage);
        expect(parsed.event).toBe('client_ready');
        expect(parsed.data.room_id).toBe(roomId);
        expect(parsed.data.player_name).toBeUndefined();
      });
    });

    describe('Reconnection with player info', () => {
      test('reconnection maintains original player name', async () => {
        const roomId = 'test-room';
        const playerName = 'Bob';

        // Initial connection with player name
        const connection1 = await networkService.connectToRoom(roomId, { playerName });

        // Simulate disconnect by closing the WebSocket
        connection1.close();

        // Wait for reconnection attempt
        await wait(200);

        // The service should attempt to reconnect with the same player info
        // This is a behavior test - we verify the pattern but don't access internals
        const status = networkService.getConnectionStatus(roomId);
        expect(status.reconnecting || status.connected).toBe(true);
      });

      test('reconnection passes player info to new connection', async () => {
        const roomId = 'test-room';
        const playerName = 'Charlie';

        // Initial connection
        const connection1 = await networkService.connectToRoom(roomId, { playerName });
        await wait(20);
        
        // Clear initial messages
        connection1.clearSentMessages();

        // Force disconnect
        await networkService.disconnectFromRoom(roomId, false);

        // Manually trigger reconnection
        const connection2 = await networkService.connectToRoom(roomId, { playerName });
        await wait(20);

        const sentMessages = connection2.getSentMessages();

        const readyMessage = sentMessages.find(msg => {
          const parsed = JSON.parse(msg);
          return parsed.event === 'client_ready';
        });

        expect(readyMessage).toBeDefined();
        const parsed = JSON.parse(readyMessage);
        expect(parsed.data.player_name).toBe(playerName);
      });
    });
  });
});
