/**
 * 🌐 **NetworkService** - Robust WebSocket Connection Manager (TypeScript)
 *
 * Phase 1, Task 1.1: Foundation Services
 *
 * Features:
 * ✅ Singleton pattern for global state management
 * ✅ Auto-reconnection with exponential backoff
 * ✅ Message queuing during disconnections
 * ✅ Heartbeat/ping system for connection health
 * ✅ Event-based architecture (extends EventTarget)
 * ✅ Graceful error handling and recovery
 * ✅ Multi-room support for concurrent games
 * ✅ Sequence-numbered events for reliable delivery
 * ✅ Full TypeScript type safety
 */

import type {
  NetworkConfig,
  ConnectionData,
  ReconnectState,
  NetworkMessage,
  ConnectionStatus,
  NetworkStatus,
  ConnectionEventDetail,
  ReconnectionEventDetail,
  NetworkEventDetail,
} from './types';
import { TIMING, GAME, NETWORK } from '../constants';

export class NetworkService extends EventTarget {
  // Singleton instance
  private static instance: NetworkService | null = null;

  /**
   * Get the singleton instance
   */
  static getInstance(): NetworkService {
    if (!NetworkService.instance) {
      NetworkService.instance = new NetworkService();
    }
    return NetworkService.instance;
  }

  private readonly config: Required<NetworkConfig>;
  private readonly connections = new Map<string, ConnectionData>();
  private readonly messageQueues = new Map<string, NetworkMessage[]>();
  private readonly sequenceNumbers = new Map<string, number>();
  private readonly heartbeatTimers = new Map<string, NodeJS.Timeout>();
  private readonly reconnectStates = new Map<string, ReconnectState>();
  private isDestroyed = false;

  private constructor() {
    super();

    if (NetworkService.instance) {
      throw new Error(
        'NetworkService is a singleton. Use NetworkService.getInstance()'
      );
    }

    // Default configuration
    this.config = {
      baseUrl: NETWORK.WEBSOCKET_BASE_URL,
      heartbeatInterval: TIMING.HEARTBEAT_INTERVAL,
      maxReconnectAttempts: GAME.MAX_RECONNECT_ATTEMPTS,
      reconnectBackoff: [...NETWORK.RECONNECT_BACKOFF],
      messageQueueLimit: GAME.MESSAGE_QUEUE_LIMIT,
      connectionTimeout: TIMING.CONNECTION_TIMEOUT,
    };
  }

  // ===== PUBLIC API =====

  /**
   * Connect to a room
   * @param roomId - The room ID to connect to
   * @param playerInfo - Optional player information for connection tracking
   */
  async connectToRoom(roomId: string, playerInfo?: { playerName?: string }): Promise<WebSocket> {
    if (this.isDestroyed) {
      throw new Error('NetworkService has been destroyed');
    }

    if (!roomId) {
      throw new Error('Room ID is required');
    }

    // Close existing connection to this room
    if (this.connections.has(roomId)) {
      await this.disconnectFromRoom(roomId);
    }

    const url = `${this.config.baseUrl}/${roomId}`;

    try {
      const connection = await this.createConnection(url, roomId);

      // Initialize room state
      this.connections.set(roomId, {
        websocket: connection,
        roomId,
        url,
        status: 'connected',
        connectedAt: Date.now(),
        messagesSent: 0,
        messagesReceived: 0,
        lastActivity: Date.now(),
        latency: null,
        playerName: playerInfo?.playerName,
      });

      this.messageQueues.set(roomId, []);
      this.sequenceNumbers.set(roomId, 0);
      this.reconnectStates.set(roomId, {
        attempts: 0,
        isReconnecting: false,
        abortController: null,
      });

      // Start heartbeat monitoring
      this.startHeartbeat(roomId);

      // Send initial ready signal
      const connectionData = this.connections.get(roomId);
      this.send(roomId, 'client_ready', { 
        room_id: roomId,
        player_name: connectionData?.playerName,
        is_reconnection: connectionData?.isReconnection || false
      });

      // Process any queued messages
      this.processQueuedMessages(roomId);

      // Reset reconnection flag after successful connection
      if (connectionData) {
        connectionData.isReconnection = false;
      }

      // Emit connection event
      this.dispatchEvent(
        new CustomEvent<ConnectionEventDetail>('connected', {
          detail: { roomId, url, timestamp: Date.now() },
        })
      );

      console.log(`🌐 NetworkService: Connected to room ${roomId}`);
      return connection;
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Unknown error';
      this.dispatchEvent(
        new CustomEvent<ConnectionEventDetail>('connectionFailed', {
          detail: { roomId, timestamp: Date.now() },
        })
      );
      throw new Error(`Failed to connect to ${roomId}: ${errorMessage}`);
    }
  }

  /**
   * Disconnect from a room
   */
  async disconnectFromRoom(roomId: string, intentional = true): Promise<void> {
    const connectionData = this.connections.get(roomId);
    if (!connectionData) return;

    // Stop reconnection if in progress
    this.stopReconnection(roomId);

    // Stop heartbeat
    this.stopHeartbeat(roomId);

    // Close WebSocket
    if (connectionData.websocket) {
      connectionData.websocket.close(1000, 'Client disconnect');
    }

    // Clean up state
    this.connections.delete(roomId);
    if (intentional) {
      this.messageQueues.delete(roomId);
      this.sequenceNumbers.delete(roomId);
    }
    this.reconnectStates.delete(roomId);

    this.dispatchEvent(
      new CustomEvent<ConnectionEventDetail>('disconnected', {
        detail: { roomId, intentional, timestamp: Date.now() },
      })
    );

    console.log(`🌐 NetworkService: Disconnected from room ${roomId}`);
  }

  /**
   * Send message to a room
   */
  send(roomId: string, event: string, data: Record<string, any> = {}): boolean {
    if (this.isDestroyed) {
      console.warn('Cannot send message: NetworkService destroyed');
      return false;
    }

    const sequenceNumber = this.getNextSequenceNumber(roomId);
    const message: NetworkMessage = {
      event,
      data,
      sequence: sequenceNumber,
      timestamp: Date.now(),
      id: crypto.randomUUID(),
    };

    const connectionData = this.connections.get(roomId);

    if (connectionData?.websocket?.readyState === WebSocket.OPEN) {
      // Send immediately
      try {
        connectionData.websocket.send(JSON.stringify(message));
        connectionData.messagesSent++;
        connectionData.lastActivity = Date.now();

        this.dispatchEvent(
          new CustomEvent<NetworkEventDetail>('messageSent', {
            detail: { roomId, message, timestamp: Date.now() },
          })
        );

        return true;
      } catch (error) {
        console.error(`Failed to send message to ${roomId}:`, error);
        this.queueMessage(roomId, message);
        return false;
      }
    } else {
      // Queue for later delivery
      this.queueMessage(roomId, message);
      console.log(
        `📤 Queued message for ${roomId}: ${event} (${this.getQueueSize(roomId)} queued)`
      );
      return false;
    }
  }

  /**
   * Get connection status for a room
   */
  getConnectionStatus(roomId: string): ConnectionStatus {
    const connectionData = this.connections.get(roomId);
    const reconnectState = this.reconnectStates.get(roomId);
    const queueSize = this.getQueueSize(roomId);

    if (!connectionData) {
      return {
        roomId,
        status: 'disconnected',
        connected: false,
        queueSize,
        reconnecting: reconnectState?.isReconnecting || false,
      };
    }

    return {
      roomId,
      status: connectionData.status,
      connected: connectionData.websocket?.readyState === WebSocket.OPEN,
      connectedAt: connectionData.connectedAt,
      uptime: Date.now() - connectionData.connectedAt,
      messagesSent: connectionData.messagesSent,
      messagesReceived: connectionData.messagesReceived,
      lastActivity: connectionData.lastActivity,
      latency: connectionData.latency,
      queueSize,
      reconnecting: reconnectState?.isReconnecting || false,
      reconnectAttempts: reconnectState?.attempts || 0,
    };
  }

  /**
   * Get status for all connections
   */
  getStatus(): NetworkStatus {
    const rooms: Record<string, ConnectionStatus> = {};
    for (const roomId of this.connections.keys()) {
      rooms[roomId] = this.getConnectionStatus(roomId);
    }

    return {
      isDestroyed: this.isDestroyed,
      activeConnections: this.connections.size,
      totalQueuedMessages: Array.from(this.messageQueues.values()).reduce(
        (total, queue) => total + queue.length,
        0
      ),
      rooms,
    };
  }

  /**
   * Destroy the service and clean up all resources
   */
  destroy(): void {
    this.isDestroyed = true;

    // Disconnect from all rooms
    const roomIds = Array.from(this.connections.keys());
    for (const roomId of roomIds) {
      this.disconnectFromRoom(roomId, true);
    }

    // Clear all state
    this.connections.clear();
    this.messageQueues.clear();
    this.sequenceNumbers.clear();
    this.heartbeatTimers.clear();
    this.reconnectStates.clear();

    // Reset singleton
    NetworkService.instance = null;

    console.log('🌐 NetworkService: Destroyed');
  }

  // ===== PRIVATE METHODS =====

  /**
   * Create a WebSocket connection
   */
  private async createConnection(
    url: string,
    roomId: string
  ): Promise<WebSocket> {
    return new Promise((resolve, reject) => {
      const websocket = new WebSocket(url);

      const timeout = setTimeout(() => {
        websocket.close();
        reject(new Error(`Connection timeout to ${url}`));
      }, this.config.connectionTimeout);

      websocket.onopen = () => {
        clearTimeout(timeout);
        this.handleConnectionOpen(roomId);
        resolve(websocket);
      };

      websocket.onmessage = (event) => {
        this.handleConnectionMessage(event, roomId);
      };

      websocket.onclose = (event) => {
        clearTimeout(timeout);
        this.handleConnectionClose(event, roomId);
      };

      websocket.onerror = () => {
        clearTimeout(timeout);
        this.handleConnectionError(roomId);
        reject(new Error(`WebSocket connection failed to ${url}`));
      };
    });
  }

  /**
   * Handle connection open
   */
  private handleConnectionOpen(roomId: string): void {
    console.log(`🔗 Connection opened to room ${roomId}`);
  }

  /**
   * Handle incoming message
   */
  private handleConnectionMessage(event: MessageEvent, roomId: string): void {
    const connectionData = this.connections.get(roomId);
    if (!connectionData) return;

    try {
      const message = JSON.parse(event.data) as NetworkMessage;
      connectionData.messagesReceived++;
      connectionData.lastActivity = Date.now();

      // Handle heartbeat response
      if (message.event === 'pong' && message.data?.timestamp) {
        connectionData.latency = Date.now() - message.data.timestamp;
        return;
      }

      // Emit the specific event
      this.dispatchEvent(
        new CustomEvent<NetworkEventDetail>(message.event, {
          detail: {
            roomId,
            data: message.data,
            message,
            timestamp: Date.now(),
          },
        })
      );

      // Also emit a general message event
      this.dispatchEvent(
        new CustomEvent<NetworkEventDetail>('message', {
          detail: { roomId, message, timestamp: Date.now() },
        })
      );
    } catch (error) {
      console.error(`Failed to parse message from ${roomId}:`, error);
      this.dispatchEvent(
        new CustomEvent<NetworkEventDetail>('messageError', {
          detail: {
            roomId,
            error: error instanceof Error ? error.message : 'Parse error',
            timestamp: Date.now(),
          },
        })
      );
    }
  }

  /**
   * Handle connection close
   */
  private handleConnectionClose(event: CloseEvent, roomId: string): void {
    const connectionData = this.connections.get(roomId);
    if (!connectionData) return;

    const wasConnected = connectionData.status === 'connected';
    connectionData.status = 'disconnected';

    this.stopHeartbeat(roomId);

    this.dispatchEvent(
      new CustomEvent<ConnectionEventDetail>('disconnected', {
        detail: {
          roomId,
          code: event.code,
          reason: event.reason,
          wasClean: event.wasClean,
          intentional: event.code === 1000,
          timestamp: Date.now(),
        },
      })
    );

    // Attempt reconnection if it wasn't intentional and we were connected
    if (wasConnected && event.code !== 1000 && !this.isDestroyed) {
      this.attemptReconnection(roomId);
    }
  }

  /**
   * Handle connection error
   */
  private handleConnectionError(roomId: string): void {
    console.error(`WebSocket error for room ${roomId}`);

    this.dispatchEvent(
      new CustomEvent<NetworkEventDetail>('connectionError', {
        detail: { roomId, error: 'Connection error', timestamp: Date.now() },
      })
    );
  }

  /**
   * Attempt automatic reconnection
   */
  private async attemptReconnection(roomId: string): Promise<void> {
    const reconnectState = this.reconnectStates.get(roomId);
    if (!reconnectState || reconnectState.isReconnecting) return;

    if (reconnectState.attempts >= this.config.maxReconnectAttempts) {
      this.dispatchEvent(
        new CustomEvent<ReconnectionEventDetail>('reconnectionFailed', {
          detail: {
            roomId,
            attempts: reconnectState.attempts,
            reason: 'Max attempts reached',
            timestamp: Date.now(),
          },
        })
      );
      return;
    }

    reconnectState.isReconnecting = true;
    reconnectState.abortController = new AbortController();

    this.dispatchEvent(
      new CustomEvent<ReconnectionEventDetail>('reconnecting', {
        detail: {
          roomId,
          attempt: reconnectState.attempts + 1,
          timestamp: Date.now(),
        },
      })
    );

    try {
      const delay = this.calculateReconnectDelay(reconnectState.attempts);
      console.log(
        `🔄 Reconnecting to ${roomId} in ${delay}ms (attempt ${reconnectState.attempts + 1})`
      );

      await new Promise<void>((resolve, reject) => {
        const timer = setTimeout(resolve, delay);
        reconnectState.abortController!.signal.addEventListener('abort', () => {
          clearTimeout(timer);
          reject(new Error('Reconnection aborted'));
        });
      });

      if (reconnectState.abortController!.signal.aborted) return;

      // Preserve player info for reconnection
      const connectionData = this.connections.get(roomId);
      const playerName = connectionData?.playerName;

      reconnectState.attempts++;
      // Mark this as a reconnection attempt
      if (connectionData) {
        connectionData.isReconnection = true;
      }
      await this.connectToRoom(roomId, { playerName });

      // Success - reset attempts
      reconnectState.attempts = 0;
      reconnectState.isReconnecting = false;

      this.dispatchEvent(
        new CustomEvent<ReconnectionEventDetail>('reconnected', {
          detail: { roomId, timestamp: Date.now() },
        })
      );
    } catch (error) {
      if (!reconnectState.abortController!.signal.aborted) {
        console.error(
          `Reconnection attempt ${reconnectState.attempts} failed for ${roomId}:`,
          error
        );

        // Try again if under limit
        if (reconnectState.attempts < this.config.maxReconnectAttempts) {
          setTimeout(() => this.attemptReconnection(roomId), 1000);
        } else {
          reconnectState.isReconnecting = false;
          this.dispatchEvent(
            new CustomEvent<ReconnectionEventDetail>('reconnectionFailed', {
              detail: {
                roomId,
                attempts: reconnectState.attempts,
                error: error instanceof Error ? error.message : 'Unknown error',
                timestamp: Date.now(),
              },
            })
          );
        }
      }
    }
  }

  /**
   * Calculate reconnection delay with exponential backoff
   */
  private calculateReconnectDelay(attempt: number): number {
    const backoffIndex = Math.min(
      attempt,
      this.config.reconnectBackoff.length - 1
    );
    const delay = this.config.reconnectBackoff[backoffIndex];

    // Add jitter (±10%)
    const jitter = delay * 0.1;
    return delay + (Math.random() * 2 - 1) * jitter;
  }

  /**
   * Start heartbeat monitoring for a room
   */
  private startHeartbeat(roomId: string): void {
    this.stopHeartbeat(roomId);

    const timer = setInterval(() => {
      const connectionData = this.connections.get(roomId);
      if (connectionData?.websocket?.readyState === WebSocket.OPEN) {
        this.send(roomId, 'ping', { timestamp: Date.now() });
      } else {
        this.stopHeartbeat(roomId);
      }
    }, this.config.heartbeatInterval);

    this.heartbeatTimers.set(roomId, timer);
  }

  /**
   * Stop heartbeat monitoring for a room
   */
  private stopHeartbeat(roomId: string): void {
    const timer = this.heartbeatTimers.get(roomId);
    if (timer) {
      clearInterval(timer);
      this.heartbeatTimers.delete(roomId);
    }
  }

  /**
   * Stop reconnection for a room
   */
  private stopReconnection(roomId: string): void {
    const reconnectState = this.reconnectStates.get(roomId);
    if (reconnectState?.abortController) {
      reconnectState.abortController.abort();
      reconnectState.isReconnecting = false;
    }
  }

  /**
   * Queue a message for later delivery
   */
  private queueMessage(roomId: string, message: NetworkMessage): void {
    let queue = this.messageQueues.get(roomId);
    if (!queue) {
      queue = [];
      this.messageQueues.set(roomId, queue);
    }

    // Prevent queue overflow
    if (queue.length >= this.config.messageQueueLimit) {
      queue.shift(); // Remove oldest message
      console.warn(`Message queue full for ${roomId}, dropping oldest message`);
    }

    queue.push(message);

    this.dispatchEvent(
      new CustomEvent<NetworkEventDetail>('messageQueued', {
        detail: { roomId, message, timestamp: Date.now() },
      })
    );
  }

  /**
   * Process queued messages for a room
   */
  private processQueuedMessages(roomId: string): void {
    const queue = this.messageQueues.get(roomId);
    if (!queue || queue.length === 0) return;

    const connectionData = this.connections.get(roomId);
    if (
      !connectionData?.websocket ||
      connectionData.websocket.readyState !== WebSocket.OPEN
    ) {
      return;
    }

    console.log(`📤 Processing ${queue.length} queued messages for ${roomId}`);

    const messages = [...queue];
    queue.length = 0; // Clear queue

    for (const message of messages) {
      try {
        connectionData.websocket.send(JSON.stringify(message));
        connectionData.messagesSent++;
      } catch (error) {
        console.error(`Failed to send queued message to ${roomId}:`, error);
        queue.push(message); // Re-queue failed message
      }
    }
  }

  /**
   * Get next sequence number for a room
   */
  private getNextSequenceNumber(roomId: string): number {
    const current = this.sequenceNumbers.get(roomId) || 0;
    const next = current + 1;
    this.sequenceNumbers.set(roomId, next);
    return next;
  }

  /**
   * Get queue size for a room
   */
  private getQueueSize(roomId: string): number {
    return this.messageQueues.get(roomId)?.length || 0;
  }
}

// Export singleton instance for immediate use
export const networkService = NetworkService.getInstance();

// Also export the class for testing purposes
export default NetworkService;
