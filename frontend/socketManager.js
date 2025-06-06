// frontend/socketManager.js

let socket; // Declare a variable to hold the WebSocket instance.
const listeners = {}; // An object to store callback functions for different event types.

let reconnectAttempts = 0;
const maxReconnectAttempts = 5;
let reconnectTimeout = null;
let isIntentionalClose = false;
let currentRoomId = null;

let connectionInProgress = false;
let connectionQueue = [];

/**
 * Establishes a WebSocket connection to the specified room with auto-reconnect.
 * @param {string} roomId - The ID of the room to connect to.
 */
export function connect(roomId) {
  if (connectionInProgress) {
    console.log(`Connection in progress, queueing request for room ${roomId}`);
    connectionQueue.push(roomId);
    return;
  }

  connectionInProgress = true;

  // Prevent duplicate connections to same room
  if (
    currentRoomId === roomId &&
    socket &&
    socket.readyState === WebSocket.OPEN
  ) {
    console.log(`Already connected to room ${roomId}, skipping reconnect`);
    return;
  }

  if (socket) {
    console.log(
      `Closing existing WebSocket before connecting to room: ${roomId}`
    );
    isIntentionalClose = true; // Mark as intentional to prevent reconnect
    socket.close();
    socket = null;
  }

  currentRoomId = roomId;
  isIntentionalClose = false;

  // ✅ Clear any existing reconnect timeout
  if (reconnectTimeout) {
    clearTimeout(reconnectTimeout);
    reconnectTimeout = null;
  }

  _createConnection(roomId);

  socket.onopen = () => {
    connectionInProgress = false;
    // Process queued connections
    if (connectionQueue.length > 0) {
      const nextRoom = connectionQueue.shift();
      if (nextRoom !== currentRoomId) {
        connect(nextRoom);
      }
    }
  };
}

/**
 * ✅ Internal function to create WebSocket connection
 */
function _createConnection(roomId) {
  try {
    socket = new WebSocket(`ws://localhost:5050/ws/${roomId}`);

    socket.onopen = () => {
      console.log(`✅ WebSocket connected to room: ${roomId}`);
      reconnectAttempts = 0; // Reset on successful connection

      // ✅ Notify UI about successful connection
      if (listeners["connected"]) {
        listeners["connected"].forEach((fn) => fn());
      }

      // Send ready signal
      emit("client_ready", { room_id: roomId });
    };

    socket.onmessage = (event) => {
      console.log("[WebSocket] Raw message received:", event.data);
      try {
        const message = JSON.parse(event.data);
        console.log("[WebSocket] Parsed message:", message);
        const eventName = message.event;
        const data = message.data;

        if (listeners[eventName]) {
          console.log(
            `[WebSocket] Triggering listeners for event: ${eventName}`
          );
          listeners[eventName].forEach((fn) => fn(data));
        } else {
          console.warn(`[WebSocket] No listener for event: ${eventName}`, data);
        }
      } catch (error) {
        console.error("[WebSocket] Failed to parse message:", error);
      }
    };

    socket.onclose = (event) => {
      console.log(`⚠️ WebSocket disconnected from room ${roomId}:`, event);

      // ✅ Only attempt reconnect if not intentional close
      if (!isIntentionalClose && reconnectAttempts < maxReconnectAttempts) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 10000); // Exponential backoff, max 10s
        reconnectAttempts++;

        console.log(
          `🔄 Attempting reconnect ${reconnectAttempts}/${maxReconnectAttempts} in ${delay}ms...`
        );

        // ✅ Show reconnection status to user
        if (listeners["reconnecting"]) {
          listeners["reconnecting"].forEach((fn) =>
            fn({
              attempt: reconnectAttempts,
              maxAttempts: maxReconnectAttempts,
              delay: delay,
            })
          );
        }

        reconnectTimeout = setTimeout(() => {
          _createConnection(currentRoomId);
        }, delay);
      } else if (reconnectAttempts >= maxReconnectAttempts) {
        console.error("❌ Max reconnection attempts reached");
        // ✅ Notify UI about connection failure
        if (listeners["connection_failed"]) {
          listeners["connection_failed"].forEach((fn) =>
            fn({
              reason: "Max reconnection attempts reached",
              attempts: reconnectAttempts,
            })
          );
        }
      }

      // ✅ Notify about disconnection
      if (listeners["disconnected"]) {
        listeners["disconnected"].forEach((fn) => fn(event));
      }
    };

    socket.onerror = (error) => {
      console.error("❌ WebSocket error:", error);

      // ✅ Notify about errors
      if (listeners["error"]) {
        listeners["error"].forEach((fn) => fn(error));
      }
    };
  } catch (error) {
    console.error("❌ Failed to create WebSocket connection:", error);

    // ✅ Retry connection after delay on creation failure
    if (reconnectAttempts < maxReconnectAttempts) {
      const delay = 2000 * (reconnectAttempts + 1);
      reconnectAttempts++;

      console.log(`🔄 Retrying connection in ${delay}ms...`);
      reconnectTimeout = setTimeout(() => {
        _createConnection(roomId);
      }, delay);
    }
  }
}

/**
 * Emits an event with associated data to the WebSocket server.
 * This function is used by the client to send messages to the server.
 * @param {string} event - The name of the event to emit.
 * @param {object} data - The data to send along with the event.
 */
export function emit(event, data) {
  if (socket && socket.readyState === WebSocket.OPEN) {
    try {
      socket.send(JSON.stringify({ event, data }));
    } catch (error) {
      console.error(`❌ Failed to send event '${event}':`, error);

      // ✅ Queue message for retry when reconnected
      if (listeners["message_failed"]) {
        listeners["message_failed"].forEach((fn) => fn({ event, data, error }));
      }
    }
  } else {
    console.warn(
      `⚠️ WebSocket not ready (state: ${socket?.readyState}). Cannot emit event: ${event}`
    );

    // ✅ Queue message for when connection is restored
    if (listeners["message_queued"]) {
      listeners["message_queued"].forEach((fn) => fn({ event, data }));
    }
  }
}

/**
 * Registers a callback function to be executed when a specific event is received from the server.
 * @param {string} event - The name of the event to listen for.
 * @param {function} fn - The callback function to execute when the event occurs.
 */
export function on(event, fn) {
  if (typeof fn !== "function") {
    console.error(`❌ Event listener for '${event}' must be a function`);
    return;
  }

  if (!listeners[event]) listeners[event] = [];
  listeners[event].push(fn);
}

/**
 * Unregisters a callback function from a specific event.
 * This is important for cleanup to prevent memory leaks and unintended behavior.
 * @param {string} event - The name of the event from which to remove the listener.
 * @param {function} fn - The specific callback function to remove.
 */
export function off(event, fn) {
  if (listeners[event]) {
    if (fn) {
      // Remove specific function
      listeners[event] = listeners[event].filter((callback) => callback !== fn);
    } else {
      // Remove all listeners for this event
      listeners[event] = [];
    }
  }
}

/**
 * Closes the WebSocket connection.
 */
export function disconnect() {
  isIntentionalClose = true; // Mark as intentional

  // ✅ Clear reconnect timeout
  if (reconnectTimeout) {
    clearTimeout(reconnectTimeout);
    reconnectTimeout = null;
  }

  // ✅ Close socket
  if (socket) {
    socket.close();
    socket = null;
  }

  // ✅ Reset state
  reconnectAttempts = 0;
  currentRoomId = null;

  // ✅ Clear all listeners
  Object.keys(listeners).forEach((event) => {
    listeners[event] = [];
  });
}

/**
 * Returns the current ready state of the WebSocket connection.
 * @returns {number|null} The ready state (0=CONNECTING, 1=OPEN, 2=CLOSING, 3=CLOSED) or null if no socket.
 */
export function getSocketReadyState() {
  if (!socket) return { state: null, text: "No connection" };

  const stateMap = {
    [WebSocket.CONNECTING]: "Connecting",
    [WebSocket.OPEN]: "Connected",
    [WebSocket.CLOSING]: "Closing",
    [WebSocket.CLOSED]: "Closed",
  };

  return {
    state: socket.readyState,
    text: stateMap[socket.readyState] || "Unknown",
  };
}

export function getConnectionStatus() {
  return {
    readyState: socket?.readyState || WebSocket.CLOSED,
    isConnected: socket?.readyState === WebSocket.OPEN,
    reconnectAttempts: reconnectAttempts,
    maxReconnectAttempts: maxReconnectAttempts,
    currentRoom: currentRoomId,
  };
}
