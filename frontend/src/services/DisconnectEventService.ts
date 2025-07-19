// frontend/src/services/DisconnectEventService.ts

/**
 * Service to handle disconnect-related WebSocket events
 * Integrates with NetworkService to provide disconnect event handling
 */

import { networkService } from './NetworkService';
import type { NetworkEventDetail } from './types';
import {
  PlayerDisconnectedEvent,
  PlayerReconnectedEvent,
  AIActivatedEvent,
  FullStateSyncEvent,
  ReconnectionSummaryEvent,
  DISCONNECT_EVENT_NAMES,
} from '../types/events';

export interface DisconnectEventHandlers {
  onPlayerDisconnected?: (data: PlayerDisconnectedEvent['data']) => void;
  onPlayerReconnected?: (data: PlayerReconnectedEvent['data']) => void;
  onAIActivated?: (data: AIActivatedEvent['data']) => void;
  onFullStateSync?: (data: FullStateSyncEvent['data']) => void;
  onReconnectionSummary?: (data: ReconnectionSummaryEvent['data']) => void;
}

export class DisconnectEventService {
  private static instance: DisconnectEventService | null = null;
  private eventListeners: Map<string, EventListener> = new Map();
  private activeRooms: Set<string> = new Set();
  private handlers: DisconnectEventHandlers = {};

  static getInstance(): DisconnectEventService {
    if (!DisconnectEventService.instance) {
      DisconnectEventService.instance = new DisconnectEventService();
    }
    return DisconnectEventService.instance;
  }

  private constructor() {
    // Setup default logging handlers
    this.handlers = {
      onPlayerDisconnected: (data) => {
        console.log('🔌 Player disconnected:', data.player_name, {
          aiActivated: data.ai_activated,
          phase: data.phase,
          canReconnect: data.can_reconnect,
        });
      },
      onPlayerReconnected: (data) => {
        console.log('🔗 Player reconnected:', data.player_name, {
          botDeactivated: data.bot_deactivated,
          phase: data.phase,
        });
      },
      onAIActivated: (data) => {
        console.log('🤖 AI activated for:', data.player_name, {
          phase: data.phase,
          reason: data.reason,
        });
      },
      onFullStateSync: (data) => {
        console.log('🔄 Full state sync for:', data.reconnected_player, {
          phase: data.phase,
          round: data.round,
        });
      },
      onReconnectionSummary: (data) => {
        console.log('📋 Reconnection summary for:', data.player_name, {
          missedEvents: data.missed_events.length,
          currentPhase: data.current_state.phase,
        });
      },
    };
  }

  /**
   * Initialize disconnect event handling for a room
   */
  initializeRoom(roomId: string): void {
    if (this.activeRooms.has(roomId)) {
      console.warn(`Disconnect events already initialized for room ${roomId}`);
      return;
    }

    this.activeRooms.add(roomId);
    this.setupEventListeners();
    console.log(`✅ Disconnect event handling initialized for room ${roomId}`);
  }

  /**
   * Clean up event handling for a room
   */
  cleanupRoom(roomId: string): void {
    this.activeRooms.delete(roomId);
    
    if (this.activeRooms.size === 0) {
      this.removeEventListeners();
    }
    
    console.log(`🧹 Disconnect event handling cleaned up for room ${roomId}`);
  }

  /**
   * Set custom event handlers
   */
  setHandlers(handlers: Partial<DisconnectEventHandlers>): void {
    this.handlers = { ...this.handlers, ...handlers };
  }

  /**
   * Update a specific handler
   */
  updateHandler<K extends keyof DisconnectEventHandlers>(
    eventType: K,
    handler: DisconnectEventHandlers[K]
  ): void {
    this.handlers[eventType] = handler;
  }

  /**
   * Get disconnected players from phase change data
   */
  getDisconnectedPlayers(players: Record<string, any>): string[] {
    return Object.entries(players)
      .filter(([_, player]) => 
        player.is_bot && !player.is_connected
      )
      .map(([name]) => name);
  }

  /**
   * Setup event listeners on NetworkService
   */
  private setupEventListeners(): void {
    // Player disconnected
    const disconnectListener = ((event: CustomEvent<NetworkEventDetail>) => {
      const data = event.detail.data as PlayerDisconnectedEvent['data'];
      this.handlers.onPlayerDisconnected?.(data);
      
      // Dispatch custom event for UI components
      window.dispatchEvent(new CustomEvent('player_disconnected', { detail: data }));
    }) as EventListener;
    
    networkService.addEventListener(DISCONNECT_EVENT_NAMES.PLAYER_DISCONNECTED, disconnectListener);
    this.eventListeners.set(DISCONNECT_EVENT_NAMES.PLAYER_DISCONNECTED, disconnectListener);

    // Player reconnected
    const reconnectListener = ((event: CustomEvent<NetworkEventDetail>) => {
      const data = event.detail.data as PlayerReconnectedEvent['data'];
      this.handlers.onPlayerReconnected?.(data);
      
      window.dispatchEvent(new CustomEvent('player_reconnected', { detail: data }));
    }) as EventListener;
    
    networkService.addEventListener(DISCONNECT_EVENT_NAMES.PLAYER_RECONNECTED, reconnectListener);
    this.eventListeners.set(DISCONNECT_EVENT_NAMES.PLAYER_RECONNECTED, reconnectListener);

    // AI activated
    const aiListener = ((event: CustomEvent<NetworkEventDetail>) => {
      const data = event.detail.data as AIActivatedEvent['data'];
      this.handlers.onAIActivated?.(data);
      
      window.dispatchEvent(new CustomEvent('ai_activated', { detail: data }));
    }) as EventListener;
    
    networkService.addEventListener(DISCONNECT_EVENT_NAMES.AI_ACTIVATED, aiListener);
    this.eventListeners.set(DISCONNECT_EVENT_NAMES.AI_ACTIVATED, aiListener);

    // Full state sync
    const syncListener = ((event: CustomEvent<NetworkEventDetail>) => {
      const data = event.detail.data as FullStateSyncEvent['data'];
      this.handlers.onFullStateSync?.(data);
      
      window.dispatchEvent(new CustomEvent('full_state_sync', { detail: data }));
    }) as EventListener;
    
    networkService.addEventListener(DISCONNECT_EVENT_NAMES.FULL_STATE_SYNC, syncListener);
    this.eventListeners.set(DISCONNECT_EVENT_NAMES.FULL_STATE_SYNC, syncListener);

    // Reconnection summary
    const summaryListener = ((event: CustomEvent<NetworkEventDetail>) => {
      const data = event.detail.data as ReconnectionSummaryEvent['data'];
      this.handlers.onReconnectionSummary?.(data);
      
      window.dispatchEvent(new CustomEvent('reconnection_summary', { detail: data }));
    }) as EventListener;
    
    networkService.addEventListener(DISCONNECT_EVENT_NAMES.RECONNECTION_SUMMARY, summaryListener);
    this.eventListeners.set(DISCONNECT_EVENT_NAMES.RECONNECTION_SUMMARY, summaryListener);

    // Phase change (for connection status updates)
    const phaseListener = ((event: CustomEvent<NetworkEventDetail>) => {
      const data = event.detail.data;
      
      // Check if phase change includes player connection info
      if (data.players) {
        const disconnectedPlayers = this.getDisconnectedPlayers(data.players);
        
        window.dispatchEvent(new CustomEvent('connection_status_update', { 
          detail: {
            players: data.players,
            disconnectedPlayers,
            phase: data.new_phase || data.phase,
          }
        }));
      }
    }) as EventListener;
    
    networkService.addEventListener('phase_change', phaseListener);
    this.eventListeners.set('phase_change', phaseListener);
  }

  /**
   * Remove all event listeners
   */
  private removeEventListeners(): void {
    this.eventListeners.forEach((listener, eventName) => {
      networkService.removeEventListener(eventName, listener);
    });
    this.eventListeners.clear();
  }

  /**
   * Get active room count
   */
  getActiveRoomCount(): number {
    return this.activeRooms.size;
  }

  /**
   * Check if room is active
   */
  isRoomActive(roomId: string): boolean {
    return this.activeRooms.has(roomId);
  }
}

// Export singleton instance
export const disconnectEventService = DisconnectEventService.getInstance();