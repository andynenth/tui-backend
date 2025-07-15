// Mock NetworkService for Jest testing
import MockWebSocket from '../../../__mocks__/websocket.js';

export class NetworkService {
  static instance = null;

  constructor() {
    if (NetworkService.instance) {
      return NetworkService.instance;
    }
    if (new.target === NetworkService) {
      throw new Error('NetworkService is a singleton. Use getInstance() instead.');
    }
  }

  static getInstance() {
    if (!NetworkService.instance) {
      NetworkService.instance = Object.create(NetworkService.prototype);
      NetworkService.instance._init();
    }
    return NetworkService.instance;
  }

  _init() {
    this.connections = new Map();
    this.messageQueues = new Map();
    this.sequenceNumbers = new Map();
    this.reconnectTimeouts = new Map();
    this.eventTarget = new EventTarget();
    this.isDestroyed = false;
  }

  async connectToRoom(roomId) {
    if (this.isDestroyed) {
      throw new Error('NetworkService has been destroyed');
    }
    if (!roomId) {
      throw new Error('Room ID is required');
    }

    // Close existing connection first
    const existingConnection = this.connections.get(roomId);
    if (existingConnection) {
      existingConnection.websocket.close();
    }

    const mockWebSocket = new MockWebSocket(`ws://localhost:5050/ws/${roomId}`);
    
    // Override the mockReceive to trigger our events
    const originalMockReceive = mockWebSocket.mockReceive.bind(mockWebSocket);
    mockWebSocket.mockReceive = (data) => {
      originalMockReceive(data);
      // Also trigger our event system
      setTimeout(() => {
        if (typeof data === 'string') {
          try {
            data = JSON.parse(data);
          } catch (e) {
            // Handle malformed JSON
            this.eventTarget.dispatchEvent(new CustomEvent('messageError', {
              detail: { roomId, error: 'Malformed message' }
            }));
            return;
          }
        }
        
        if (data.event === 'pong') {
          // Update latency
          const connection = this.connections.get(roomId);
          if (connection) {
            connection.latency = Date.now() - data.data.timestamp;
          }
        }
        
        this.eventTarget.dispatchEvent(new CustomEvent(data.event || 'message', {
          detail: { roomId, data: data.data || data, message: data }
        }));
      }, 0);
    };
    
    // Override mockError to trigger our events
    mockWebSocket.mockError = (error = 'Mock error') => {
      setTimeout(() => {
        this.eventTarget.dispatchEvent(new CustomEvent('connectionError', {
          detail: { roomId, error: 'Connection error' }
        }));
      }, 0);
    };

    this.connections.set(roomId, { 
      websocket: mockWebSocket,
      latency: 50,
      connectedAt: Date.now()
    });
    this.messageQueues.set(roomId, []);
    this.sequenceNumbers.set(roomId, 0);

    // Wait for WebSocket to be "open" then send ready message
    setTimeout(() => {
      this.send(roomId, 'client_ready', { room_id: roomId });
      
      // Emit connected event
      this.eventTarget.dispatchEvent(new CustomEvent('connected', {
        detail: { roomId, url: mockWebSocket.url }
      }));
    }, 10); // Small delay to let MockWebSocket open

    return mockWebSocket;
  }

  async disconnectFromRoom(roomId, intentional = true) {
    const connection = this.connections.get(roomId);
    if (connection) {
      connection.websocket.close(1000, 'Client disconnect');
      this.connections.delete(roomId);
      
      setTimeout(() => {
        this.eventTarget.dispatchEvent(new CustomEvent('disconnected', {
          detail: { roomId, intentional }
        }));
      }, 0);
    }
  }

  send(roomId, event, data) {
    if (this.isDestroyed) return false;
    
    const connection = this.connections.get(roomId);
    if (!connection) {
      const queue = this.messageQueues.get(roomId) || [];
      queue.push({ event, data });
      this.messageQueues.set(roomId, queue);
      return false;
    }

    const sequence = this.sequenceNumbers.get(roomId) + 1;
    this.sequenceNumbers.set(roomId, sequence);

    const message = {
      event,
      data,
      sequence,
      id: Math.random().toString(36),
      timestamp: Date.now()
    };

    connection.websocket.send(JSON.stringify(message));
    return true;
  }

  getConnectionStatus(roomId) {
    const connection = this.connections.get(roomId);
    if (!connection) {
      return {
        roomId,
        status: 'disconnected',
        connected: false,
        reconnecting: false
      };
    }

    return {
      roomId,
      status: 'connected',
      connected: true,
      queueSize: this.messageQueues.get(roomId)?.length || 0,
      reconnecting: false,
      reconnectAttempts: 0,
      connectedAt: connection.connectedAt,
      uptime: Date.now() - connection.connectedAt,
      latency: connection.latency || 50
    };
  }

  getStatus() {
    return {
      isDestroyed: this.isDestroyed,
      activeConnections: this.connections.size,
      totalQueuedMessages: Array.from(this.messageQueues.values())
        .reduce((total, queue) => total + queue.length, 0),
      rooms: Object.fromEntries(
        Array.from(this.connections.keys()).map(roomId => [
          roomId,
          this.getConnectionStatus(roomId)
        ])
      )
    };
  }

  addEventListener(type, listener) {
    this.eventTarget.addEventListener(type, listener);
  }

  removeEventListener(type, listener) {
    this.eventTarget.removeEventListener(type, listener);
  }

  destroy() {
    this.connections.forEach(connection => {
      connection.websocket.close(1000, 'Service destroyed');
    });
    this.connections.clear();
    this.messageQueues.clear();
    this.sequenceNumbers.clear();
    this.isDestroyed = true;
    NetworkService.instance = null;
  }
}

export const networkService = NetworkService.getInstance();