// Timing Constants (in milliseconds)
export const TIMING = {
  // Network
  HEARTBEAT_INTERVAL: 30000,
  CONNECTION_TIMEOUT: 10000,
  RECOVERY_TIMEOUT: 60000,
  ERROR_WINDOW_MS: 300000,

  // Animation
  DEALING_ANIMATION_DURATION: 3500,
  TURN_FLIP_DELAY: 800,
  TURN_RESULTS_REVEAL_DELAY: 200,
  PLAYER_ANIMATION_STAGGER: 100,

  // UI Feedback
  CREATE_ROOM_DELAY: 100,
  REFRESH_ANIMATION_DURATION: 1000,
  CHECKMARK_DISPLAY_DURATION: 500,

  // Timers
  DEFAULT_COUNTDOWN_DURATION: 5,
} as const;

// Type for TIMING keys
export type TimingKey = keyof typeof TIMING;

// Game Configuration Constants
export const GAME = {
  MAX_PLAYERS: 4,
  MAX_RECONNECT_ATTEMPTS: 10,
  MESSAGE_QUEUE_LIMIT: 1000,
  EVENT_BUFFER_SIZE: 1000,
} as const;

// Type for GAME keys
export type GameConfigKey = keyof typeof GAME;

// Network Configuration Constants
export const NETWORK = {
  RECONNECT_BACKOFF: [1000, 2000, 4000, 8000, 16000] as const,
  // Build WebSocket URL dynamically based on current location
  get WEBSOCKET_BASE_URL(): string {
    if (typeof window !== 'undefined') {
      // In development, always use the backend port 5050
      if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        return 'ws://localhost:5050/ws';
      }
      // In production, use the same host
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      return `${protocol}//${host}/ws`;
    }
    // Fallback for server-side rendering or tests
    return 'ws://localhost:5050/ws';
  },
} as const;

// Type for NETWORK keys
export type NetworkConfigKey = keyof typeof NETWORK;

// Export all types for convenience
export type Constants = {
  TIMING: typeof TIMING;
  GAME: typeof GAME;
  NETWORK: typeof NETWORK;
};
