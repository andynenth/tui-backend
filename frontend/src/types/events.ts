// frontend/src/types/events.ts

/**
 * Disconnect-related event type definitions for WebSocket communication
 */

// Player disconnect event
export interface PlayerDisconnectedEvent {
  event: 'player_disconnected';
  data: {
    player_name: string;
    ai_activated: boolean;
    phase: string;
    actions_taken: string[];
    can_reconnect: boolean;
    is_bot: boolean;
    timestamp?: string;
  };
}

// Player reconnect event
export interface PlayerReconnectedEvent {
  event: 'player_reconnected';
  data: {
    player_name: string;
    bot_deactivated: boolean;
    phase: string;
    timestamp?: string;
  };
}

// AI activation event
export interface AIActivatedEvent {
  event: 'ai_activated';
  data: {
    player_name: string;
    phase: string;
    reason: string;
    timestamp?: string;
  };
}

// Full state sync event (for reconnection)
export interface FullStateSyncEvent {
  event: 'full_state_sync';
  data: {
    phase: string;
    allowed_actions: string[];
    phase_data: any;
    players: Record<string, any>;
    round: number;
    reconnected_player: string;
    timestamp: string;
  };
}

// Reconnection summary event
export interface ReconnectionSummaryEvent {
  event: 'reconnection_summary';
  data: {
    player_name: string;
    missed_events: Array<{
      event: string;
      summary: string;
      timestamp: string;
    }>;
    current_state: {
      phase: string;
      round: number;
      current_player?: string;
    };
  };
}

// Phase change event (enhanced with connection info)
export interface PhaseChangeEvent {
  event: 'phase_change';
  data: {
    new_phase: string;
    phase_data: any;
    players?: Record<string, {
      name: string;
      is_bot: boolean;
      is_connected: boolean;
      score?: number;
      hand_size?: number;
    }>;
    round?: number;
    timestamp?: string;
  };
}

// Connection status update event
export interface ConnectionStatusUpdateEvent {
  event: 'connection_status_update';
  data: {
    room_id: string;
    players: Record<string, {
      is_connected: boolean;
      is_bot: boolean;
      disconnect_time?: string;
    }>;
    timestamp: string;
  };
}

// Union type for all disconnect-related events
export type DisconnectRelatedEvent = 
  | PlayerDisconnectedEvent
  | PlayerReconnectedEvent
  | AIActivatedEvent
  | FullStateSyncEvent
  | ReconnectionSummaryEvent
  | PhaseChangeEvent
  | ConnectionStatusUpdateEvent;

// Event names for type safety
export const DISCONNECT_EVENT_NAMES = {
  PLAYER_DISCONNECTED: 'player_disconnected',
  PLAYER_RECONNECTED: 'player_reconnected',
  AI_ACTIVATED: 'ai_activated',
  FULL_STATE_SYNC: 'full_state_sync',
  RECONNECTION_SUMMARY: 'reconnection_summary',
  PHASE_CHANGE: 'phase_change',
  CONNECTION_STATUS_UPDATE: 'connection_status_update',
} as const;

// Type guard functions
export function isPlayerDisconnectedEvent(event: any): event is PlayerDisconnectedEvent {
  return event?.event === 'player_disconnected';
}

export function isPlayerReconnectedEvent(event: any): event is PlayerReconnectedEvent {
  return event?.event === 'player_reconnected';
}

export function isAIActivatedEvent(event: any): event is AIActivatedEvent {
  return event?.event === 'ai_activated';
}

export function isFullStateSyncEvent(event: any): event is FullStateSyncEvent {
  return event?.event === 'full_state_sync';
}

export function isReconnectionSummaryEvent(event: any): event is ReconnectionSummaryEvent {
  return event?.event === 'reconnection_summary';
}