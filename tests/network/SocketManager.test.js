// ===== tests/network/SocketManager.test.js =====
import { SocketManager } from '../../frontend/network/SocketManager.js';
import { MessageQueue } from '../../frontend/network/MessageQueue.js';

describe('SocketManager', () => {
  let socketManager;
  let mockWebSocket;
  
  beforeEach(() => {
    // Mock WebSocket
    global.WebSocket = jest.fn(() => {
      mockWebSocket = {
        readyState: WebSocket.CONNECTING,
        send: jest.fn(),
        close: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn()
      };
      
      // Simulate connection after a delay
      setTimeout(() => {
        mockWebSocket.readyState = WebSocket.OPEN;
        mockWebSocket.onopen?.();
      }, 10);
      
      return mockWebSocket;
    });
    
    socketManager = new SocketManager({
      baseUrl: 'ws://localhost:5050/ws',
      enableReconnection: true,
      enableMessageQueue: true
    });
  });
  
  afterEach(() => {
    socketManager.disconnect();
    jest.clearAllMocks();
  });
  
  describe('Connection Management', () => {
    test('should connect to a room', async () => {
      const roomId = 'TEST123';
      await socketManager.connect(roomId);
      
      expect(global.WebSocket).toHaveBeenCalledWith(`ws://localhost:5050/ws/${roomId}`);
      expect(socketManager.getStatus().connected).toBe(true);
      expect(socketManager.getStatus().roomId).toBe(roomId);
    });
    
    test('should handle connection failure', async () => {
      global.WebSocket = jest.fn(() => {
        const ws = {
          readyState: WebSocket.CONNECTING,
          close: jest.fn()
        };
        setTimeout(() => ws.onerror?.(new Error('Connection failed')), 10);
        return ws;
      });
      
      await expect(socketManager.connect('TEST123')).rejects.toThrow();
      expect(socketManager.getStatus().connected).toBe(false);
    });
    
    test('should disconnect cleanly', async () => {
      await socketManager.connect('TEST123');
      socketManager.disconnect();
      
      expect(mockWebSocket.close).toHaveBeenCalled();
      expect(socketManager.getStatus().connected).toBe(false);
      expect(socketManager.getStatus().roomId).toBe(null);
    });
  });
  
  describe('Message Handling', () => {
    test('should send messages when connected', async () => {
      await socketManager.connect('TEST123');
      
      const sent = socketManager.send('test_event', { data: 'test' });
      
      expect(sent).toBe(true);
      expect(mockWebSocket.send).toHaveBeenCalledWith(
        JSON.stringify({ event: 'test_event', data: { data: 'test' } })
      );
    });
    
    test('should queue messages when disconnected', () => {
      const sent = socketManager.send('test_event', { data: 'test' });
      
      expect(sent).toBe(false);
      expect(socketManager.getStatus().queueSize).toBe(1);
    });
    
    test('should process queued messages on reconnect', async () => {
      // Queue messages while disconnected
      socketManager.send('event1', { data: 1 });
      socketManager.send('event2', { data: 2 });
      
      expect(socketManager.getStatus().queueSize).toBe(2);
      
      // Connect
      await socketManager.connect('TEST123');
      
      // Check that queued messages were sent
      expect(mockWebSocket.send).toHaveBeenCalledTimes(3); // 2 queued + 1 ready signal
      expect(socketManager.getStatus().queueSize).toBe(0);
    });
  });
  
  describe('Event System', () => {
    test('should emit events to listeners', async () => {
      const mockHandler = jest.fn();
      socketManager.on('test_event', mockHandler);
      
      await socketManager.connect('TEST123');
      
      // Simulate incoming message
      mockWebSocket.onmessage?.({
        data: JSON.stringify({ event: 'test_event', data: { value: 42 } })
      });
      
      expect(mockHandler).toHaveBeenCalledWith({ value: 42 });
    });
    
    test('should support unsubscribing', async () => {
      const mockHandler = jest.fn();
      const unsubscribe = socketManager.on('test_event', mockHandler);
      
      await socketManager.connect('TEST123');
      
      // Unsubscribe
      unsubscribe();
      
      // Simulate message
      mockWebSocket.onmessage?.({
        data: JSON.stringify({ event: 'test_event', data: {} })
      });
      
      expect(mockHandler).not.toHaveBeenCalled();
    });
  });
  
  describe('Reconnection', () => {
    test('should attempt reconnection on unexpected disconnect', async () => {
      const reconnectingHandler = jest.fn();
      socketManager.on('reconnecting', reconnectingHandler);
      
      await socketManager.connect('TEST123');
      
      // Simulate unexpected disconnect
      mockWebSocket.onclose?.({ code: 1006, reason: 'Abnormal closure' });
      
      // Wait for reconnection attempt
      await new Promise(resolve => setTimeout(resolve, 1100));
      
      expect(reconnectingHandler).toHaveBeenCalled();
      expect(socketManager.getStatus().reconnection.attempts).toBeGreaterThan(0);
    });
    
    test('should not reconnect on intentional disconnect', async () => {
      const reconnectingHandler = jest.fn();
      socketManager.on('reconnecting', reconnectingHandler);
      
      await socketManager.connect('TEST123');
      socketManager.disconnect();
      
      // Simulate close event
      mockWebSocket.onclose?.({ code: 1000, reason: 'Normal closure' });
      
      await new Promise(resolve => setTimeout(resolve, 100));
      
      expect(reconnectingHandler).not.toHaveBeenCalled();
    });
  });
});