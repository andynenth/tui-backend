/**
 * 🔧 **Services Module** - Foundation Services (TypeScript)
 * 
 * Phase 1: Foundation Services for robust architecture
 * Provides core services for network communication and state management
 */

// Core Services
export { NetworkService, networkService } from './NetworkService';
export { GameService, gameService } from './GameService';
export { RecoveryService, recoveryService } from './RecoveryService';
export { ServiceIntegration, serviceIntegration } from './ServiceIntegration';

// Types
export type * from './types';

// Service initialization and health monitoring (Task 1.4)
// ✅ RecoveryService (Task 1.3) - Complete
// ✅ ServiceIntegration (Task 1.4) - Complete

import { serviceIntegration } from './ServiceIntegration';
import type { ServiceHealthStatus } from './types';

/**
 * Service Health Status (via Integration Layer)
 */
export function getServicesHealth(): ServiceHealthStatus {
  return serviceIntegration.getHealthStatus();
}

/**
 * Initialize all services via Integration Layer
 */
export async function initializeServices(): Promise<void> {
  await serviceIntegration.initialize();
}

/**
 * Cleanup all services via Integration Layer
 */
export function cleanupServices(): void {
  serviceIntegration.destroy();
}

/**
 * Connect to a game room with full integration
 */
export async function connectToRoom(roomId: string, playerName: string): Promise<void> {
  await serviceIntegration.connectToRoom(roomId, playerName);
}

/**
 * Disconnect from current room with cleanup
 */
export async function disconnectFromRoom(): Promise<void> {
  await serviceIntegration.disconnectFromRoom();
}

/**
 * Trigger manual error recovery
 */
export async function triggerRecovery(errorType?: string) {
  return await serviceIntegration.triggerRecovery(errorType);
}

/**
 * Emergency reset all services
 */
export async function emergencyReset(): Promise<void> {
  await serviceIntegration.emergencyReset();
}