// frontend/src/services/index.ts

/**
 * 🔧 **Services Module** - Foundation Services (TypeScript)
 * 
 * Phase 1: Foundation Services for robust architecture
 * Provides core services for network communication and state management
 */

// Core Services
export { NetworkService, networkService } from './NetworkService';
export { RecoveryService, recoveryService } from './RecoveryService';

// Types
export type * from './types';

// New simplified initialization using NetworkIntegration
import { networkIntegration } from '../stores/NetworkIntegration';
import { networkService } from './NetworkService';
import { gameStore } from '../stores/UnifiedGameStore';

/**
 * Initialize all services
 */
export async function initializeServices(): Promise<void> {
  // Initialize network integration to bridge store and network
  networkIntegration.initialize();
}

/**
 * Cleanup all services
 */
export function cleanupServices(): void {
  networkIntegration.cleanup();
}

/**
 * Connect to a game room
 */
export async function connectToRoom(roomId: string, playerName: string): Promise<void> {
  // Set player name in store
  gameStore.setState({ playerName });
  
  // Connect via network service
  await networkService.connectToRoom(roomId);
}

/**
 * Disconnect from current room
 */
export async function disconnectFromRoom(): Promise<void> {
  const { roomId } = gameStore.getState();
  if (roomId) {
    await networkService.disconnectFromRoom(roomId);
  }
}