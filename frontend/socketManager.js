// frontend/socketManager.js

let socket; // Declare a variable to hold the WebSocket instance.
const listeners = {}; // An object to store callback functions for different event types.

/**
 * Establishes a WebSocket connection to the specified room.
 * @param {string} roomId - The ID of the room to connect to.
 */
export function connect(roomId) {
    // Check if a WebSocket connection already exists and is open.
    if (socket && socket.readyState === WebSocket.OPEN) {
        console.warn("WebSocket already connected.");
        return; // If already connected, do nothing.
    }

    // Create a new WebSocket instance, connecting to the backend server with the specified room ID.
    socket = new WebSocket(`ws://localhost:5050/ws/${roomId}`);

    // Event handler for when the WebSocket connection is successfully opened.
    socket.onopen = () => {
        console.log(`WebSocket connected to room: ${roomId}`);
        // IMPORTANT: Once the WebSocket is open, inform the backend that the client is ready.
        // This is crucial for initial setup or synchronization.
        emit('client_ready', { room_id: roomId }); // Emit a 'client_ready' event to the server.
        // Trigger any registered 'connected' listeners.
        if (listeners['connected']) listeners['connected'].forEach(fn => fn());
    };

    // Event handler for when a message is received from the WebSocket server.
    socket.onmessage = (event) => {
        console.log("[WebSocket] Raw message received:", event.data); // Log the raw message data for debugging.
        const message = JSON.parse(event.data); // Parse the incoming JSON message.
        console.log("[WebSocket] Parsed message:", message); // Log the parsed message object.
        const eventName = message.event; // Extract the event name from the message.
        const data = message.data; // Extract the associated data.

        // Check if there are any registered listeners for the received event name.
        if (listeners[eventName]) {
            console.log(`[WebSocket] Triggering listeners for event: ${eventName}`); // Log that listeners are being triggered.
            // Iterate over all registered callback functions for this event and call them with the data.
            listeners[eventName].forEach((fn) => fn(data));
        } else {
            // Warn if no listener is found for the received event.
            console.warn(`[WebSocket] No listener for event: ${eventName}`, data);
        }
    };

    // Event handler for when the WebSocket connection is closed.
    socket.onclose = (event) => {
        console.log("WebSocket disconnected:", event);
        // Trigger any registered 'disconnected' listeners.
        if (listeners["disconnected"])
            listeners["disconnected"].forEach((fn) => fn(event));
    };

    // Event handler for WebSocket errors.
    socket.onerror = (error) => {
        console.error("WebSocket error:", error);
        // Trigger any registered 'error' listeners.
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
    // Check if a socket instance exists.
    if (socket) {
        socket.close(); // Close the WebSocket connection.
        socket = null; // Clear the socket instance.
    }
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
