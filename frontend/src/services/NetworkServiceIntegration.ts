// frontend/src/services/NetworkServiceIntegration.ts

/**
 * Integration module to connect NetworkService with disconnect event handling
 * This ensures the existing NetworkService works with our new disconnect features
 */

import { networkService } from './NetworkService';
import { disconnectEventService } from './DisconnectEventService';
import type { DisconnectEventHandlers } from './DisconnectEventService';

export class NetworkServiceIntegration {
  private static isInitialized = false;
  private static currentRoomId: string | null = null;

  /**
   * Initialize the integration for a game room
   */
  static initializeForRoom(roomId: string, handlers?: Partial<DisconnectEventHandlers>): void {
    if (this.currentRoomId === roomId && this.isInitialized) {
      console.log('Network integration already initialized for room:', roomId);
      return;
    }

    // Clean up previous room if different
    if (this.currentRoomId && this.currentRoomId !== roomId) {
      this.cleanup();
    }

    this.currentRoomId = roomId;
    
    // Set custom handlers if provided
    if (handlers) {
      disconnectEventService.setHandlers(handlers);
    }

    // Initialize disconnect event handling
    disconnectEventService.initializeRoom(roomId);
    
    this.isInitialized = true;
    console.log('✅ Network service integration initialized for room:', roomId);
  }

  /**
   * Update event handlers dynamically
   */
  static updateHandlers(handlers: Partial<DisconnectEventHandlers>): void {
    disconnectEventService.setHandlers(handlers);
  }

  /**
   * Clean up integration
   */
  static cleanup(): void {
    if (this.currentRoomId) {
      disconnectEventService.cleanupRoom(this.currentRoomId);
      this.currentRoomId = null;
    }
    this.isInitialized = false;
    console.log('🧹 Network service integration cleaned up');
  }

  /**
   * Get current room ID
   */
  static getCurrentRoomId(): string | null {
    return this.currentRoomId;
  }

  /**
   * Check if integration is active
   */
  static isActive(): boolean {
    return this.isInitialized;
  }

  /**
   * Helper to send disconnect test events (for development)
   */
  static sendTestDisconnectEvent(playerName: string): void {
    if (!this.isInitialized) {
      console.warn('Integration not initialized');
      return;
    }

    // Simulate a disconnect event
    const event = new CustomEvent('player_disconnected', {
      detail: {
        player_name: playerName,
        ai_activated: true,
        phase: 'turn',
        actions_taken: ['bot_activated'],
        can_reconnect: true,
        is_bot: true,
        timestamp: new Date().toISOString(),
      }
    });

    window.dispatchEvent(event);
  }

  /**
   * Helper to send reconnect test events (for development)
   */
  static sendTestReconnectEvent(playerName: string): void {
    if (!this.isInitialized) {
      console.warn('Integration not initialized');
      return;
    }

    // Simulate a reconnect event
    const event = new CustomEvent('player_reconnected', {
      detail: {
        player_name: playerName,
        bot_deactivated: true,
        phase: 'turn',
        timestamp: new Date().toISOString(),
      }
    });

    window.dispatchEvent(event);
  }
}

// For convenience, export the NetworkService instance and methods
export { networkService } from './NetworkService';
export { disconnectEventService } from './DisconnectEventService';

// Helper function to initialize everything at once
export function initializeNetworkWithDisconnectHandling(
  roomId: string,
  handlers?: Partial<DisconnectEventHandlers>
): Promise<WebSocket> {
  // Initialize integration
  NetworkServiceIntegration.initializeForRoom(roomId, handlers);
  
  // Connect to room
  return networkService.connectToRoom(roomId);
}