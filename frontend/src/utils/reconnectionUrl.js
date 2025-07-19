// frontend/src/utils/reconnectionUrl.js

/**
 * Utility for generating reconnection URLs
 * Instead of direct navigation to /game/roomId, we redirect through
 * the start page with query parameters
 */

/**
 * Generate a reconnection URL
 * @param {string} roomId - The room ID to reconnect to
 * @param {string} playerName - The player name
 * @returns {string} The reconnection URL
 */
export function generateReconnectionUrl(roomId, playerName) {
  const baseUrl = window.location.origin;
  const params = new URLSearchParams({
    rejoin: roomId,
    player: playerName,
  });

  return `${baseUrl}/?${params.toString()}`;
}

/**
 * Parse reconnection parameters from URL
 * @returns {Object|null} Reconnection data or null if not present
 */
export function parseReconnectionParams() {
  const params = new URLSearchParams(window.location.search);
  const roomId = params.get('rejoin');
  const playerName = params.get('player');

  if (roomId && playerName) {
    return { roomId, playerName };
  }

  return null;
}

/**
 * Clear reconnection parameters from URL
 * This should be called after successful reconnection
 */
export function clearReconnectionParams() {
  const url = new URL(window.location);
  url.searchParams.delete('rejoin');
  url.searchParams.delete('player');

  // Update URL without reload
  window.history.replaceState({}, document.title, url.toString());
}

/**
 * Handle direct navigation attempts to game URLs
 * This intercepts 404 errors and redirects to reconnection URL
 */
export function setupReconnectionHandler() {
  // Listen for navigation errors
  window.addEventListener('error', (event) => {
    // Check if it's a navigation error
    if (event.target === window) {
      const path = window.location.pathname;

      // Check if it's a game URL
      const gameMatch = path.match(/^\/game\/([A-Z0-9]+)$/);
      if (gameMatch) {
        const roomId = gameMatch[1];

        // Check if we have session data
        const sessionData = localStorage.getItem('liap_tui_session');
        if (sessionData) {
          try {
            const session = JSON.parse(sessionData);
            if (session.roomId === roomId) {
              // Redirect to reconnection URL
              window.location.href = generateReconnectionUrl(
                session.roomId,
                session.playerName
              );
              event.preventDefault();
            }
          } catch (error) {
            console.error('Failed to parse session data:', error);
          }
        }
      }
    }
  });
}
