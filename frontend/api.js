// frontend/api.js

console.log("📡 API module loaded"); // Log a message to the console when this API module is loaded.

/**
 * Sends a request to the backend to create a new game room.
 * @param {string} name - The name of the host creating the room.
 * @returns {Promise<object>} A promise that resolves with the room details (e.g., { room_id: "...", host_name: "..." }).
 * @throws {Error} If the JSON response cannot be parsed.
 */
export async function createRoom(name) {
  // Send a POST request to the '/api/create-room' endpoint, including the host's name as a query parameter.
  const res = await fetch(`/api/create-room?name=${encodeURIComponent(name)}`, {
    method: 'POST', // Specify the HTTP method as POST.
  });
  const text = await res.text(); // Get the response body as plain text.
  try {
    // Attempt to parse the response text as JSON.
    // Expected response format: { room_id: "...", host_name: "..." }
    return JSON.parse(text);
  } catch (err) {
    // Log an error if JSON parsing fails and re-throw the error.
    console.error("❌ Failed to parse JSON:", text);
    throw err;
  }
}

/**
 * Sends a request to the backend to get a list of all available game rooms.
 * @returns {Promise<Array<object>>} A promise that resolves with an array of room objects.
 */
export async function listRooms() {
  // Send a GET request to the '/api/list-rooms' endpoint.
  const res = await fetch(`/api/list-rooms`);
  return res.json(); // Parse and return the JSON response.
}

/**
 * Sends a request to the backend to join an existing game room.
 * Handles both successful responses and API errors.
 * @param {string} roomId - The ID of the room to join.
 * @param {string} name - The name of the player joining the room.
 * @returns {Promise<object>} A promise that resolves with room details if successful.
 * @throws {Error} If the request fails or the API returns an error.
 */
export async function joinRoom(roomId, name) {
    // Send a POST request to the backend API to join a room.
    const res = await fetch(`/api/join-room?room_id=${roomId}&name=${name}`, {
        method: 'POST',
    });
    
    // Check if the HTTP response indicates an error (status code outside 200-299 range).
    if (!res.ok) {
        // Parse the error details from the response body.
        const errorData = await res.json();
        // Create and throw an Error object with details from the backend.
        const error = new Error(errorData.detail || 'Failed to join room');
        error.status = res.status; // Attach the HTTP status code.
        throw error;
    }
    
    // If the response is successful, parse and return the JSON data.
    return res.json();
}

/**
 * Sends a request to the backend to start a game within a specific room.
 * @param {string} roomId - The ID of the room where the game should start.
 * @returns {Promise<object>} A promise that resolves with the game start confirmation.
 */
export async function startGame(roomId) {
  // Send a POST request to the '/api/start-game' endpoint, with the room ID.
  const res = await fetch(`/api/start-game?room_id=${roomId}`, { method: 'POST' });
  return res.json(); // Parse and return the JSON response.
}

/**
 * Sends a request to the backend to assign a player to a specific slot in a room.
 * @param {string} roomId - The ID of the room.
 * @param {string} name - The name of the player to assign.
 * @param {number} slot - The slot number to assign the player to.
 * @returns {Promise<object>} A promise that resolves with the assignment confirmation.
 */
export async function assignSlot(roomId, name, slot) {
  // If name is null or undefined, don't include it in the query string
  let url = `/api/assign-slot?room_id=${roomId}&slot=${slot}`;
  
  // Only add name parameter if it's not null
  if (name !== null && name !== undefined) {
    url += `&name=${encodeURIComponent(name)}`;
  }
  
  const res = await fetch(url, {
    method: 'POST',
  });
  return res.json();
}

/**
 * Sends a request to the backend to get the current state data of a specific room.
 * Renamed from `getRoomState` to `getRoomStateData` to avoid confusion.
 * @param {string} roomId - The ID of the room to get state data for.
 * @returns {Promise<object>} A promise that resolves with the room's state (e.g., { room_id: "...", host_name: "...", slots: {...}, started: false }).
 * @throws {Error} If the JSON response cannot be parsed.
 */
export async function getRoomStateData(roomId) {
  // Send a GET request to the '/api/get-room-state' endpoint with the room ID.
  const res = await fetch(`/api/get-room-state?room_id=${roomId}`);
  const text = await res.text(); // Get the response body as plain text.
  try {
    // Attempt to parse the response text as JSON.
    // Expected return value: { room_id: "...", host_name: "...", slots: {...}, started: false }
    return JSON.parse(text);
  } catch (err) {
    // Log an error if JSON parsing fails and re-throw the error.
    console.error("❌ Failed to parse JSON for getRoomStateData:", text);
    throw err;
  }
}
