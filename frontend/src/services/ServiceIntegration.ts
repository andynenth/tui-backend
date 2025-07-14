/**
 * 🔗 **ServiceIntegration** - Unified Service Layer with Global Error Handling (TypeScript)
 *
 * Phase 1, Task 1.4: Foundation Services Integration
 *
 * Features:
 * ✅ Unified service initialization and lifecycle management
 * ✅ Global error handling and recovery coordination
 * ✅ Cross-service event orchestration
 * ✅ Service health monitoring and diagnostics
 * ✅ Automatic error recovery workflows
 * ✅ Performance monitoring and metrics
 * ✅ Full TypeScript type safety
 */

import { networkService } from './NetworkService';
import { gameService } from './GameService';
import { recoveryService } from './RecoveryService';
import { TIMING } from '../constants';
import type {
  IntegrationConfig,
  ServiceError,
  ErrorRecoveryResult,
  ServiceHealthStatus,
  IntegrationStatus,
  ErrorSeverity,
  RecoveryStrategy,
  ServiceMetrics,
  IntegrationEventDetail,
} from './types';

export class ServiceIntegration extends EventTarget {
  // Singleton instance
  private static instance: ServiceIntegration | null = null;

  /**
   * Get the singleton instance
   */
  static getInstance(): ServiceIntegration {
    if (!ServiceIntegration.instance) {
      ServiceIntegration.instance = new ServiceIntegration();
    }
    return ServiceIntegration.instance;
  }

  private readonly config: Required<IntegrationConfig>;
  private readonly errorHistory: ServiceError[] = [];
  private readonly metrics: ServiceMetrics = {
    totalErrors: 0,
    recoveryAttempts: 0,
    successfulRecoveries: 0,
    uptime: Date.now(),
    lastHealthCheck: 0,
  };
  private isInitialized = false;
  private isDestroyed = false;
  private healthCheckInterval: NodeJS.Timeout | null = null;
  private readonly recoveryStrategies = new Map<string, RecoveryStrategy[]>();

  private constructor() {
    super();

    if (ServiceIntegration.instance) {
      throw new Error(
        'ServiceIntegration is a singleton. Use ServiceIntegration.getInstance()'
      );
    }

    // Default configuration
    this.config = {
      healthCheckInterval: TIMING.HEARTBEAT_INTERVAL,
      errorRetention: 100, // Keep last 100 errors
      autoRecovery: true,
      recoveryTimeout: TIMING.RECOVERY_TIMEOUT,
      maxRecoveryAttempts: 3,
      errorThreshold: 10, // Alert after 10 errors in window
      errorWindowMs: TIMING.ERROR_WINDOW_MS,
      enableMetrics: true,
    };

    this.setupRecoveryStrategies();
    console.log('🔗 ServiceIntegration: Initialized');
  }

  // ===== PUBLIC API =====

  /**
   * Initialize all services with error handling
   */
  async initialize(): Promise<void> {
    if (this.isInitialized) {
      console.log('ServiceIntegration already initialized');
      return;
    }

    if (this.isDestroyed) {
      throw new Error('ServiceIntegration has been destroyed');
    }

    try {
      console.log('');
      console.log('🎯 =============================================');
      console.log('🚀 PHASE 1-4 ENTERPRISE ARCHITECTURE STARTING');
      console.log('🎯 =============================================');
      console.log('🔧 Initializing integrated service layer...');

      // Setup error listeners before initialization
      this.setupErrorListeners();

      // Initialize services in dependency order
      await this.initializeNetworkService();
      await this.initializeGameService();
      await this.initializeRecoveryService();

      // Setup cross-service integrations
      this.setupServiceIntegrations();

      // Start health monitoring
      this.startHealthMonitoring();

      this.isInitialized = true;

      this.dispatchEvent(
        new CustomEvent<IntegrationEventDetail>('initialized', {
          detail: { timestamp: Date.now() },
        })
      );

      console.log('');
      console.log('✅ =============================================');
      console.log('🎉 PHASE 1-4 ARCHITECTURE FULLY OPERATIONAL!');
      console.log('✅ =============================================');
      console.log(
        '🔗 NetworkService: Advanced WebSocket with auto-reconnection'
      );
      console.log(
        '🎮 GameService: React hooks with TypeScript state management'
      );
      console.log(
        '🛠️ RecoveryService: Automatic error recovery and health monitoring'
      );
      console.log('🏢 Enterprise Features: Event sourcing, logging, metrics');
      console.log('✅ Service integration layer initialized successfully');
      console.log('');
    } catch (error) {
      const serviceError = this.createServiceError(
        'INITIALIZATION_FAILED',
        'CRITICAL',
        error instanceof Error ? error.message : 'Unknown initialization error',
        'ServiceIntegration'
      );

      this.handleError(serviceError);
      throw new Error(
        `Service integration initialization failed: ${serviceError.message}`
      );
    }
  }

  /**
   * Connect to a game room with full integration
   */
  async connectToRoom(roomId: string, playerName: string): Promise<void> {
    if (!this.isInitialized) {
      throw new Error('ServiceIntegration not initialized');
    }

    try {
      console.log(`🔗 Connecting to room ${roomId} as ${playerName}...`);

      // Initialize recovery tracking for the room
      recoveryService.initializeRoom(roomId);

      // Connect via GameService (which uses NetworkService)
      await gameService.joinRoom(roomId, playerName);

      this.dispatchEvent(
        new CustomEvent<IntegrationEventDetail>('roomConnected', {
          detail: { roomId, playerName, timestamp: Date.now() },
        })
      );

      console.log(`✅ Successfully connected to room ${roomId}`);
    } catch (error) {
      const serviceError = this.createServiceError(
        'ROOM_CONNECTION_FAILED',
        'HIGH',
        error instanceof Error ? error.message : 'Unknown connection error',
        'ServiceIntegration',
        { roomId, playerName }
      );

      await this.handleError(serviceError);
      throw error;
    }
  }

  /**
   * Disconnect from current room with cleanup
   */
  async disconnectFromRoom(): Promise<void> {
    try {
      const gameState = gameService.getState();
      const roomId = gameState.roomId;

      if (roomId) {
        console.log(`🔗 Disconnecting from room ${roomId}...`);

        // Disconnect from game service
        await gameService.leaveRoom();

        // Cleanup recovery service
        recoveryService.cleanupRoom(roomId);

        this.dispatchEvent(
          new CustomEvent<IntegrationEventDetail>('roomDisconnected', {
            detail: { roomId, timestamp: Date.now() },
          })
        );

        console.log(`✅ Successfully disconnected from room ${roomId}`);
      }
    } catch (error) {
      const serviceError = this.createServiceError(
        'ROOM_DISCONNECTION_FAILED',
        'MEDIUM',
        error instanceof Error ? error.message : 'Unknown disconnection error',
        'ServiceIntegration'
      );

      await this.handleError(serviceError);
    }
  }

  /**
   * Get comprehensive system health status
   */
  getHealthStatus(): ServiceHealthStatus {
    const networkStatus = networkService.getStatus();
    const gameState = gameService.getState();
    const recoveryStatus = gameState.roomId
      ? recoveryService.getRecoveryStatus(gameState.roomId)
      : null;

    return {
      overall: this.calculateOverallHealth(
        networkStatus,
        gameState,
        recoveryStatus
      ),
      network: {
        healthy:
          !networkStatus.isDestroyed && networkStatus.activeConnections >= 0,
        connections: networkStatus.activeConnections,
        queuedMessages: networkStatus.totalQueuedMessages,
        status: networkStatus.isDestroyed ? 'destroyed' : 'operational',
      },
      game: {
        healthy: gameState.error === null && !gameState.gameOver,
        connected: gameState.isConnected,
        phase: gameState.phase,
        roomId: gameState.roomId,
        playersCount: gameState.players.length,
        status: gameState.error ? 'error' : 'operational',
      },
      recovery: recoveryStatus
        ? {
            healthy:
              !recoveryStatus.isRecovering && recoveryStatus.gapsDetected === 0,
            initialized: recoveryStatus.initialized,
            isRecovering: recoveryStatus.isRecovering,
            eventBufferSize: recoveryStatus.eventBufferSize,
            gapsDetected: recoveryStatus.gapsDetected,
            status: recoveryStatus.isRecovering ? 'recovering' : 'operational',
          }
        : null,
      integration: this.getIntegrationStatus(),
      metrics: { ...this.metrics },
      errors: this.getRecentErrors(5),
    };
  }

  /**
   * Manually trigger error recovery
   */
  async triggerRecovery(errorType?: string): Promise<ErrorRecoveryResult> {
    if (!this.isInitialized) {
      throw new Error('ServiceIntegration not initialized');
    }

    console.log(
      `🔄 Triggering manual recovery${errorType ? ` for ${errorType}` : ''}...`
    );

    try {
      this.metrics.recoveryAttempts++;

      // Get current game state for context
      const gameState = gameService.getState();

      // Apply recovery strategies
      const strategies = errorType
        ? this.recoveryStrategies.get(errorType) || []
        : this.getAllRecoveryStrategies();

      let recoverySuccess = false;
      const appliedStrategies: string[] = [];

      for (const strategy of strategies) {
        try {
          console.log(`🔧 Applying recovery strategy: ${strategy.name}`);
          await strategy.execute(gameState);
          appliedStrategies.push(strategy.name);
          recoverySuccess = true;
        } catch (strategyError) {
          console.warn(`Strategy ${strategy.name} failed:`, strategyError);
        }
      }

      if (recoverySuccess) {
        this.metrics.successfulRecoveries++;
        console.log(
          `✅ Recovery completed with strategies: ${appliedStrategies.join(', ')}`
        );
      }

      const result: ErrorRecoveryResult = {
        success: recoverySuccess,
        appliedStrategies,
        timestamp: Date.now(),
        errorType: errorType || 'MANUAL_RECOVERY',
      };

      this.dispatchEvent(
        new CustomEvent<IntegrationEventDetail>('recoveryCompleted', {
          detail: { recoveryResult: result, timestamp: Date.now() },
        })
      );

      return result;
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Unknown recovery error';
      console.error('❌ Recovery failed:', error);

      return {
        success: false,
        appliedStrategies: [],
        timestamp: Date.now(),
        errorType: errorType || 'MANUAL_RECOVERY',
        error: errorMessage,
      };
    }
  }

  /**
   * Get service metrics
   */
  getMetrics(): ServiceMetrics {
    return { ...this.metrics };
  }

  /**
   * Reset all services (emergency reset)
   */
  async emergencyReset(): Promise<void> {
    console.log('🚨 Performing emergency service reset...');

    try {
      // Disconnect from current room if connected
      await this.disconnectFromRoom();

      // Reset all services
      gameService.destroy();
      recoveryService.destroy();
      networkService.destroy();

      // Clear error history
      this.errorHistory.length = 0;

      // Reset metrics
      this.metrics.totalErrors = 0;
      this.metrics.recoveryAttempts = 0;
      this.metrics.successfulRecoveries = 0;
      this.metrics.uptime = Date.now();

      this.dispatchEvent(
        new CustomEvent<IntegrationEventDetail>('emergencyReset', {
          detail: { timestamp: Date.now() },
        })
      );

      console.log('✅ Emergency reset completed');
    } catch (error) {
      console.error('❌ Emergency reset failed:', error);
      throw error;
    }
  }

  /**
   * Destroy the integration layer
   */
  destroy(): void {
    this.isDestroyed = true;

    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
      this.healthCheckInterval = null;
    }

    // Cleanup all services
    recoveryService.destroy();
    gameService.destroy();
    networkService.destroy();

    // Clear state
    this.errorHistory.length = 0;
    this.recoveryStrategies.clear();

    // Reset singleton
    ServiceIntegration.instance = null;

    console.log('🔗 ServiceIntegration: Destroyed');
  }

  // ===== PRIVATE METHODS =====

  /**
   * Setup recovery strategies for different error types
   */
  private setupRecoveryStrategies(): void {
    // Network connection recovery
    this.recoveryStrategies.set('NETWORK_CONNECTION_FAILED', [
      {
        name: 'reconnect',
        execute: async (gameState) => {
          if (gameState.roomId) {
            await networkService.connectToRoom(gameState.roomId);
          }
        },
      },
    ]);

    // Sequence gap recovery
    this.recoveryStrategies.set('SEQUENCE_GAP', [
      {
        name: 'triggerRecovery',
        execute: async (gameState) => {
          if (gameState.roomId) {
            await recoveryService.startRecovery(gameState.roomId);
          }
        },
      },
    ]);

    // Game state corruption recovery
    this.recoveryStrategies.set('GAME_STATE_ERROR', [
      {
        name: 'requestStateSync',
        execute: async (gameState) => {
          if (gameState.roomId && gameState.isConnected) {
            networkService.send(gameState.roomId, 'request_state_sync', {});
          }
        },
      },
    ]);

    // Generic connection recovery
    this.recoveryStrategies.set('CONNECTION_LOST', [
      {
        name: 'reconnectAndRecover',
        execute: async (gameState) => {
          if (gameState.roomId) {
            await networkService.connectToRoom(gameState.roomId);
            await recoveryService.startRecovery(gameState.roomId);
          }
        },
      },
    ]);
  }

  /**
   * Setup error listeners for all services
   */
  private setupErrorListeners(): void {
    // Network service errors
    networkService.addEventListener('connectionFailed', (event) => {
      const customEvent = event as CustomEvent;
      const error = this.createServiceError(
        'NETWORK_CONNECTION_FAILED',
        'HIGH',
        'Network connection failed',
        'NetworkService',
        customEvent.detail
      );
      this.handleError(error);
    });

    networkService.addEventListener('connectionError', (event) => {
      const customEvent = event as CustomEvent;
      const error = this.createServiceError(
        'NETWORK_CONNECTION_ERROR',
        'MEDIUM',
        'Network connection error',
        'NetworkService',
        customEvent.detail
      );
      this.handleError(error);
    });

    // Recovery service errors
    recoveryService.addEventListener('recoveryFailed', (event) => {
      const customEvent = event as CustomEvent;
      const error = this.createServiceError(
        'RECOVERY_FAILED',
        'HIGH',
        `Recovery failed: ${customEvent.detail.error}`,
        'RecoveryService',
        customEvent.detail
      );
      this.handleError(error);
    });

    recoveryService.addEventListener('sequenceGap', (event) => {
      const customEvent = event as CustomEvent;
      const error = this.createServiceError(
        'SEQUENCE_GAP',
        'MEDIUM',
        `Sequence gap detected: ${customEvent.detail.gap.start}-${customEvent.detail.gap.end}`,
        'RecoveryService',
        customEvent.detail
      );
      this.handleError(error);
    });

    // Game service errors (would need to be added to GameService)
    gameService.addEventListener('stateChange', (event) => {
      const customEvent = event as CustomEvent;
      const gameState = customEvent.detail.state;

      if (gameState.error) {
        const error = this.createServiceError(
          'GAME_STATE_ERROR',
          'HIGH',
          gameState.error,
          'GameService',
          { phase: gameState.phase, roomId: gameState.roomId }
        );
        this.handleError(error);
      }
    });
  }

  /**
   * Setup cross-service integrations
   */
  private setupServiceIntegrations(): void {
    // Auto-initialize recovery when joining rooms
    gameService.addEventListener('stateChange', (event) => {
      const customEvent = event as CustomEvent;
      const gameState = customEvent.detail.state;

      if (gameState.roomId && gameState.isConnected) {
        const recoveryStatus = recoveryService.getRecoveryStatus(
          gameState.roomId
        );
        if (!recoveryStatus.initialized) {
          recoveryService.initializeRoom(gameState.roomId);
        }
      }
    });

    // Auto-trigger recovery on significant sequence gaps
    recoveryService.addEventListener('sequenceGap', (event) => {
      const customEvent = event as CustomEvent;
      const { roomId, gap } = customEvent.detail;

      // Trigger recovery for large gaps
      if (gap.end - gap.start >= 5) {
        console.log(`🔄 Auto-triggering recovery for large gap in ${roomId}`);
        this.triggerRecovery('SEQUENCE_GAP');
      }
    });

    // Handle connection events
    networkService.addEventListener('disconnected', (event) => {
      const customEvent = event as CustomEvent;
      if (!customEvent.detail.intentional) {
        console.log(
          '🔄 Unintentional disconnection detected, monitoring for recovery'
        );
      }
    });
  }

  /**
   * Initialize NetworkService
   */
  private async initializeNetworkService(): Promise<void> {
    // NetworkService is already initialized as singleton
    console.log('✅ NetworkService integrated');
  }

  /**
   * Initialize GameService
   */
  private async initializeGameService(): Promise<void> {
    // GameService is already initialized as singleton
    console.log('✅ GameService integrated');
  }

  /**
   * Initialize RecoveryService
   */
  private async initializeRecoveryService(): Promise<void> {
    // RecoveryService is already initialized as singleton
    console.log('✅ RecoveryService integrated');
  }

  /**
   * Start health monitoring
   */
  private startHealthMonitoring(): void {
    this.healthCheckInterval = setInterval(() => {
      this.performHealthCheck();
    }, this.config.healthCheckInterval);

    console.log(
      `🩺 Health monitoring started (${this.config.healthCheckInterval}ms interval)`
    );
  }

  /**
   * Perform health check
   */
  private performHealthCheck(): void {
    this.metrics.lastHealthCheck = Date.now();

    const health = this.getHealthStatus();

    if (!health.overall.healthy) {
      console.warn('⚠️ Health check detected issues:', health.overall.issues);

      this.dispatchEvent(
        new CustomEvent<IntegrationEventDetail>('healthIssue', {
          detail: { healthStatus: health, timestamp: Date.now() },
        })
      );

      // Auto-trigger recovery if enabled
      if (this.config.autoRecovery) {
        this.triggerRecovery();
      }
    }
  }

  /**
   * Handle service errors
   */
  private async handleError(error: ServiceError): Promise<void> {
    this.metrics.totalErrors++;
    this.errorHistory.push(error);

    // Limit error history size
    if (this.errorHistory.length > this.config.errorRetention) {
      this.errorHistory.shift();
    }

    console.error(
      `🚨 Service Error [${error.severity}] ${error.type}:`,
      error.message,
      error.context
    );

    this.dispatchEvent(
      new CustomEvent<IntegrationEventDetail>('error', {
        detail: { error, timestamp: Date.now() },
      })
    );

    // Check if we should trigger automatic recovery
    if (this.config.autoRecovery && this.shouldTriggerAutoRecovery(error)) {
      await this.triggerRecovery(error.type);
    }

    // Check error threshold
    this.checkErrorThreshold();
  }

  /**
   * Create a service error object
   */
  private createServiceError(
    type: string,
    severity: ErrorSeverity,
    message: string,
    source: string,
    context?: any
  ): ServiceError {
    return {
      type,
      severity,
      message,
      source,
      timestamp: Date.now(),
      context,
    };
  }

  /**
   * Check if auto recovery should be triggered
   */
  private shouldTriggerAutoRecovery(error: ServiceError): boolean {
    return error.severity === 'HIGH' || error.severity === 'CRITICAL';
  }

  /**
   * Check error threshold and alert if exceeded
   */
  private checkErrorThreshold(): void {
    const recentErrors = this.getRecentErrors(this.config.errorWindowMs);

    if (recentErrors.length >= this.config.errorThreshold) {
      console.warn(
        `⚠️ Error threshold exceeded: ${recentErrors.length} errors in ${this.config.errorWindowMs}ms`
      );

      this.dispatchEvent(
        new CustomEvent<IntegrationEventDetail>('errorThresholdExceeded', {
          detail: {
            errorCount: recentErrors.length,
            windowMs: this.config.errorWindowMs,
            timestamp: Date.now(),
          },
        })
      );
    }
  }

  /**
   * Get recent errors within time window
   */
  private getRecentErrors(windowMs: number): ServiceError[] {
    const cutoff = Date.now() - windowMs;
    return this.errorHistory.filter((error) => error.timestamp >= cutoff);
  }

  /**
   * Calculate overall system health
   */
  private calculateOverallHealth(
    networkStatus: any,
    gameState: any,
    recoveryStatus: any
  ): {
    healthy: boolean;
    issues: string[];
  } {
    const issues: string[] = [];

    if (networkStatus.isDestroyed) {
      issues.push('NetworkService destroyed');
    }

    if (gameState.error) {
      issues.push(`Game error: ${gameState.error}`);
    }

    if (recoveryStatus?.isRecovering) {
      issues.push('Recovery in progress');
    }

    if (recoveryStatus?.gapsDetected > 0) {
      issues.push(`Sequence gaps detected: ${recoveryStatus.gapsDetected}`);
    }

    return {
      healthy: issues.length === 0,
      issues,
    };
  }

  /**
   * Get integration status
   */
  private getIntegrationStatus(): IntegrationStatus {
    return {
      initialized: this.isInitialized,
      destroyed: this.isDestroyed,
      errorCount: this.errorHistory.length,
      lastError: this.errorHistory[this.errorHistory.length - 1] || null,
      healthCheckEnabled: this.healthCheckInterval !== null,
      autoRecoveryEnabled: this.config.autoRecovery,
    };
  }

  /**
   * Get all recovery strategies
   */
  private getAllRecoveryStrategies(): RecoveryStrategy[] {
    const allStrategies: RecoveryStrategy[] = [];
    for (const strategies of this.recoveryStrategies.values()) {
      allStrategies.push(...strategies);
    }
    return allStrategies;
  }
}

// Export singleton instance for immediate use
export const serviceIntegration = ServiceIntegration.getInstance();

// Also export the class for testing purposes
export default ServiceIntegration;
