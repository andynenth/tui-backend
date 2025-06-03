// frontend/socketManager.js

let socket; // Declare a variable to hold the WebSocket instance.
const listeners = {}; // An object to store callback functions for different event types.

/**
 * Establishes a WebSocket connection to the specified room.
 * @param {string} roomId - The ID of the room to connect to.
 */
export function connect(roomId) {
    // ✅ ปิด WebSocket เก่าก่อนเปิดใหม่
    if (socket) {
        console.log(`Closing existing WebSocket before connecting to room: ${roomId}`);
        socket.close();
        socket = null;
    }

    socket = new WebSocket(`ws://localhost:5050/ws/${roomId}`);

    socket.onopen = () => {
        console.log(`WebSocket connected to room: ${roomId}`);
        emit('client_ready', { room_id: roomId });
        if (listeners['connected']) listeners['connected'].forEach(fn => fn());
    };

    socket.onmessage = (event) => {
        console.log("[WebSocket] Raw message received:", event.data);
        const message = JSON.parse(event.data);
        console.log("[WebSocket] Parsed message:", message);
        const eventName = message.event;
        const data = message.data;

        if (listeners[eventName]) {
            console.log(`[WebSocket] Triggering listeners for event: ${eventName}`);
            listeners[eventName].forEach((fn) => fn(data));
        } else {
            console.warn(`[WebSocket] No listener for event: ${eventName}`, data);
        }
    };

    socket.onclose = (event) => {
        console.log("WebSocket disconnected:", event);
        if (listeners["disconnected"])
            listeners["disconnected"].forEach((fn) => fn(event));
    };

    socket.onerror = (error) => {
        console.error("WebSocket error:", error);
        if (listeners["error"]) listeners["error"].forEach((fn) => fn(error));
    };
}

/**
 * Emits an event with associated data to the WebSocket server.
 * This function is used by the client to send messages to the server.
 * @param {string} event - The name of the event to emit.
 * @param {object} data - The data to send along with the event.
 */
export function emit(event, data) {
    // Check if the WebSocket is open before attempting to send a message.
    if (socket && socket.readyState === WebSocket.OPEN) {
        // Send the event and data as a JSON string.
        socket.send(JSON.stringify({ event, data }));
    } else {
        // Warn if the WebSocket is not open and the event cannot be sent.
        console.warn("WebSocket not open. Cannot emit event:", event);
    }
}

/**
 * Registers a callback function to be executed when a specific event is received from the server.
 * @param {string} event - The name of the event to listen for.
 * @param {function} fn - The callback function to execute when the event occurs.
 */
export function on(event, fn) {
    // If no listeners array exists for this event, create one.
    if (!listeners[event]) listeners[event] = [];
    // Add the callback function to the list of listeners for this event.
    listeners[event].push(fn);
}

/**
 * Unregisters a callback function from a specific event.
 * This is important for cleanup to prevent memory leaks and unintended behavior.
 * @param {string} event - The name of the event from which to remove the listener.
 * @param {function} fn - The specific callback function to remove.
 */
export function off(event, fn) {
    // Check if there are listeners for this event.
    if (listeners[event]) {
        // Filter out the specific callback function from the array of listeners.
        listeners[event] = listeners[event].filter((callback) => callback !== fn);
    }
}

/**
 * Closes the WebSocket connection.
 */
export function disconnect() {
    if (socket) {
        socket.close();
        socket = null;
    }
    // ✅ Clear all listeners
    Object.keys(listeners).forEach(event => {
        listeners[event] = [];
    });
}

/**
 * Returns the current ready state of the WebSocket connection.
 * @returns {number|null} The ready state (0=CONNECTING, 1=OPEN, 2=CLOSING, 3=CLOSED) or null if no socket.
 */
export function getSocketReadyState() {
    if (socket) {
        return socket.readyState; // Return the WebSocket's readyState property.
    }
    return null; // Return null if the socket has not been initialized.
}
