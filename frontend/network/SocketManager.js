// ===== frontend/network/SocketManager.js =====
/**
 * Main SocketManager that orchestrates all components
 * This is the main entry point for WebSocket communication
 */
import { SocketConnection } from "./core/SocketConnection.js";
import { EventEmitter } from "./core/EventEmitter.js";
import { MessageQueue } from "./MessageQueue.js";
import { ConnectionMonitor } from "./ConnectionMonitor.js";
import { ReconnectionManager } from "./ReconnectionManager.js";

export class SocketManager {
  constructor(options = {}) {
    // Configuration
    this.baseUrl = options.baseUrl || `ws://localhost:5050/ws`;
    this.enableReconnection = options.enableReconnection !== false;
    this.enableMessageQueue = options.enableMessageQueue !== false;

    // Core components
    this.connection = null;
    this.eventEmitter = new EventEmitter();
    this.messageQueue = new MessageQueue(options.maxQueueSize || 100);
    this.monitor = new ConnectionMonitor();
    this.reconnectionManager = new ReconnectionManager(
      options.reconnection || {}
    );

    // State
    this.currentRoomId = null;
    this.isIntentionalDisconnect = false;

    // Bind methods to preserve context
    this._handleMessage = this._handleMessage.bind(this);
    this._handleClose = this._handleClose.bind(this);
    this._handleError = this._handleError.bind(this);
  }

  // ===== Public API =====

  async connect(roomId) {
    // Clean up any existing connection
    if (this.connection) {
      this.isIntentionalDisconnect = true;
      this.disconnect();
    }

    this.currentRoomId = roomId;
    this.isIntentionalDisconnect = false;
    const url = `${this.baseUrl}/${roomId}`;

    try {
      // Create and connect
      this.connection = new SocketConnection(url);
      await this.connection.connect();

      // Setup event handlers
      this._setupConnectionHandlers();

      // Update monitor
      this.monitor.markConnected();

      // Emit connected event
      this.eventEmitter.emit("connected", { roomId });

      // Send ready signal
      this.send("client_ready", { room_id: roomId });

      // Process any queued messages
      this._processMessageQueue();

      // Start ping monitoring
      this.monitor.startPingMonitoring(this.connection);

      return this.connection;
    } catch (error) {
      this.monitor.markDisconnected(error);
      this.eventEmitter.emit("connection_failed", { error, roomId });
      throw error;
    }
  }

  disconnect() {
    this.isIntentionalDisconnect = true;
    this.reconnectionManager.stop();
    this.monitor.stopPingMonitoring();

    if (this.connection) {
      this.connection.close();
      this.connection = null;
    }

    this.currentRoomId = null;
    this.messageQueue.clear();
    this.eventEmitter.emit("disconnected", { intentional: true });
    this.monitor.markDisconnected();
  }

  send(event, data = {}) {
    const message = { event, data };

    if (this.connection && this.connection.isConnected()) {
      const sent = this.connection.send(message);
      if (sent) {
        this.monitor.recordMessageSent();
        return true;
      }
    }

    // Queue if enabled and not connected
    if (this.enableMessageQueue) {
      this.messageQueue.enqueue(message);
      this.eventEmitter.emit("message_queued", message);
    } else {
      console.warn(`Cannot send message, not connected: ${event}`);
      this.eventEmitter.emit("message_failed", {
        message,
        reason: "Not connected",
      });
    }

    return false;
  }

  on(event, callback) {
    return this.eventEmitter.on(event, callback);
  }

  off(event, callback) {
    this.eventEmitter.off(event, callback);
  }

  getStatus() {
    return {
      ...this.monitor.getStatus(),
      roomId: this.currentRoomId,
      queueSize: this.messageQueue.size(),
      reconnection: this.reconnectionManager.getStatus(),
    };
  }

  // ===== Private Methods =====

  _setupConnectionHandlers() {
    this.connection.onMessage(this._handleMessage);
    this.connection.onClose(this._handleClose);
    this.connection.onError(this._handleError);
  }

  _handleMessage(data) {
    this.monitor.recordMessageReceived();

    // ADD COMPREHENSIVE DEBUG LOGGING
    console.log(
      "🔵 [SocketManager] RAW WebSocket message:",
      JSON.stringify(data)
    );

    // Check what format the data is in
    if (typeof data === "string") {
      console.log("📝 [SocketManager] Message is string, parsing...");
      try {
        data = JSON.parse(data);
      } catch (e) {
        console.error("❌ [SocketManager] Failed to parse string message:", e);
        return;
      }
    }

    // Log the structure
    console.log("📊 [SocketManager] Message structure:", {
      hasType: "type" in data,
      hasEvent: "event" in data,
      hasData: "data" in data,
      keys: Object.keys(data),
    });

    // Parse different message formats
    let event, eventData;

    // Handle backend format variations
    if (data.type) {
      // Backend sends: { type: "redeal_phase_started", data: {...} }
      event = data.type;
      eventData = data.data || {};
      console.log(`✅ [SocketManager] Using 'type' field: "${event}"`);
    } else if (data.event) {
      // Or: { event: "redeal_phase_started", data: {...} }
      event = data.event;
      eventData = data.data || {};
      console.log(`✅ [SocketManager] Using 'event' field: "${event}"`);
    } else {
      console.error("❌ [SocketManager] Unknown message format:", data);
      console.error(
        '   Expected: {type: "...", data: {...}} or {event: "...", data: {...}}'
      );
      return;
    }

    console.log(
      `📤 [SocketManager] Emitting event: "${event}" with data:`,
      eventData
    );

    // Handle system messages
    if (event === "pong") {
      this.monitor.recordPong(eventData.timestamp);
      return;
    }

    // Emit to listeners
    this.eventEmitter.emit(event, eventData);

    // Also emit a general message event
    this.eventEmitter.emit("message", { event, data: eventData });

    // SPECIAL DEBUG for redeal events
    if (event.includes("redeal")) {
      console.log("🎯 [SocketManager] REDEAL EVENT DETECTED!");
      console.log("   Event name:", event);
      console.log("   Event data:", eventData);
      console.log(
        "   Listeners registered:",
        this.eventEmitter.events.has(event)
      );
    }
  }

  _handleClose(event) {
    const wasConnected = this.connection && this.connection.isConnected();
    this.connection = null;

    this.monitor.markDisconnected();
    this.eventEmitter.emit("disconnected", {
      code: event.code,
      reason: event.reason,
      intentional: this.isIntentionalDisconnect,
    });

    // Attempt reconnection if enabled and not intentional
    if (
      this.enableReconnection &&
      !this.isIntentionalDisconnect &&
      wasConnected
    ) {
      this._attemptReconnection();
    }
  }

  _handleError(error) {
    console.error("WebSocket error:", error);
    this.monitor.lastError = error;
    this.eventEmitter.emit("error", error);
  }

  async _attemptReconnection() {
    this.monitor.markReconnecting();
    this.eventEmitter.emit(
      "reconnecting",
      this.reconnectionManager.getStatus()
    );

    try {
      await this.reconnectionManager.scheduleReconnect(async () => {
        // Update status for each attempt
        this.eventEmitter.emit(
          "reconnecting",
          this.reconnectionManager.getStatus()
        );

        // Try to connect
        return await this.connect(this.currentRoomId);
      });

      // Success
      this.eventEmitter.emit("reconnected", { roomId: this.currentRoomId });
    } catch (error) {
      // Failed after all attempts
      this.eventEmitter.emit("reconnection_failed", {
        error,
        attempts: this.reconnectionManager.attempts,
      });
    }
  }

  _processMessageQueue() {
    if (!this.enableMessageQueue || this.messageQueue.size() === 0) {
      return;
    }

    // Process all queued messages
    const messages = this.messageQueue.getAll();
    this.messageQueue.clear();

    messages.forEach((message) => {
      this.send(message.event, message.data);
    });

    console.log(`Processed ${messages.length} queued messages`);
  }
}
