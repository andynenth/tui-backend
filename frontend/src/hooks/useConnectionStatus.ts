/**
 * 🌐 **useConnectionStatus Hook** - Network Connection State Management (TypeScript)
 * 
 * Phase 2, Task 2.1: Clean React Hooks
 * 
 * Features:
 * ✅ Single responsibility - only connection status
 * ✅ Real-time connection monitoring
 * ✅ TypeScript interfaces for type safety
 * ✅ Network metrics and diagnostics
 * ✅ Connection health indicators
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { networkService } from '../services/NetworkService';
import { serviceIntegration } from '../services/ServiceIntegration';
import type { 
  NetworkStatus, 
  ConnectionStatus, 
  ServiceHealthStatus,
  NetworkHealthInfo
} from '../services/types';

/**
 * Connection state information
 */
export interface ConnectionState {
  // Basic connection info
  isConnected: boolean;
  isConnecting: boolean;
  isReconnecting: boolean;
  
  // Connection details
  roomId: string | null;
  connectedAt: number | null;
  uptime: number | null;
  
  // Network metrics
  latency: number | null;
  messagesSent: number;
  messagesReceived: number;
  queuedMessages: number;
  
  // Connection health
  status: 'connected' | 'disconnected' | 'connecting' | 'reconnecting' | 'error';
  error: string | null;
  reconnectAttempts: number;
  
  // Last activity
  lastActivity: number | null;
}

/**
 * Connection metrics for monitoring
 */
export interface ConnectionMetrics {
  totalConnections: number;
  uptime: number | null;
  averageLatency: number | null;
  messageRate: number;
  errorRate: number;
  reconnectionRate: number;
}

/**
 * Hook for monitoring connection status
 */
export function useConnectionStatus(roomId?: string): ConnectionState {
  const [connectionState, setConnectionState] = useState<ConnectionState>(() => 
    getInitialConnectionState(roomId)
  );

  const updateConnectionState = useCallback(() => {
    const networkStatus = networkService.getStatus();
    const healthStatus = serviceIntegration.getHealthStatus();
    
    // Get specific room status or overall status
    const roomStatus = roomId ? networkStatus.rooms[roomId] : null;
    const overallHealthy = healthStatus.network.healthy;
    
    const newState: ConnectionState = {
      isConnected: roomStatus ? roomStatus.connected : healthStatus.network.connections > 0,
      isConnecting: roomStatus?.status === 'connecting' || false,
      isReconnecting: roomStatus ? roomStatus.reconnecting : false,
      
      roomId: roomStatus?.roomId || null,
      connectedAt: roomStatus?.connectedAt || null,
      uptime: roomStatus?.uptime || null,
      
      latency: roomStatus?.latency || null,
      messagesSent: roomStatus?.messagesSent || 0,
      messagesReceived: roomStatus?.messagesReceived || 0,
      queuedMessages: roomStatus?.queueSize || healthStatus.network.queuedMessages,
      
      status: determineConnectionStatus(roomStatus, overallHealthy),
      error: roomStatus ? null : (healthStatus.network.healthy ? null : 'Network error'),
      reconnectAttempts: roomStatus?.reconnectAttempts || 0,
      
      lastActivity: roomStatus?.lastActivity || null
    };

    setConnectionState(newState);
  }, [roomId]);

  useEffect(() => {
    // Initial update
    updateConnectionState();

    // Set up event listeners for real-time updates
    const eventTypes = [
      'connected',
      'disconnected',
      'connecting',
      'reconnecting',
      'reconnected',
      'connectionFailed',
      'connectionError',
      'messageSent',
      'messageReceived'
    ];

    const handleNetworkEvent = () => {
      updateConnectionState();
    };

    // Add listeners to network service
    eventTypes.forEach(eventType => {
      networkService.addEventListener(eventType, handleNetworkEvent);
    });

    // Add listener to service integration for health changes
    serviceIntegration.addEventListener('healthIssue', handleNetworkEvent);
    serviceIntegration.addEventListener('initialized', handleNetworkEvent);

    // Set up event listeners for metrics that change over time
    serviceIntegration.addEventListener('metricsUpdated', handleNetworkEvent);
    networkService.addEventListener('metricsUpdated', handleNetworkEvent);

    return () => {
      // Cleanup event listeners
      eventTypes.forEach(eventType => {
        networkService.removeEventListener(eventType, handleNetworkEvent);
      });
      
      serviceIntegration.removeEventListener('healthIssue', handleNetworkEvent);
      serviceIntegration.removeEventListener('initialized', handleNetworkEvent);
      serviceIntegration.removeEventListener('metricsUpdated', handleNetworkEvent);
      networkService.removeEventListener('metricsUpdated', handleNetworkEvent);
    };
  }, [updateConnectionState]);

  return connectionState;
}

/**
 * Hook for accessing overall network status
 */
export function useNetworkStatus(): NetworkStatus {
  const [networkStatus, setNetworkStatus] = useState<NetworkStatus>(() => 
    networkService.getStatus()
  );

  useEffect(() => {
    const updateNetworkStatus = () => {
      setNetworkStatus(networkService.getStatus());
    };

    // Update on network events
    const eventTypes = [
      'connected',
      'disconnected',
      'messageSent',
      'messageReceived',
      'messageQueued'
    ];

    eventTypes.forEach(eventType => {
      networkService.addEventListener(eventType, updateNetworkStatus);
    });

    // Event-driven updates for service health changes
    serviceIntegration.addEventListener('healthStatusChanged', updateNetworkStatus);
    networkService.addEventListener('statusChanged', updateNetworkStatus);

    return () => {
      eventTypes.forEach(eventType => {
        networkService.removeEventListener(eventType, updateNetworkStatus);
      });
      serviceIntegration.removeEventListener('healthStatusChanged', updateNetworkStatus);
      networkService.removeEventListener('statusChanged', updateNetworkStatus);
    };
  }, []);

  return networkStatus;
}

/**
 * Hook for connection quality assessment
 */
export function useConnectionQuality(roomId?: string) {
  const connectionState = useConnectionStatus(roomId);

  return useMemo(() => {
    const { latency, isConnected, reconnectAttempts, queuedMessages, uptime } = connectionState;

    // Calculate quality score (0-100)
    let qualityScore = 0;

    if (isConnected) {
      qualityScore += 40; // Base score for being connected
      
      // Latency score (0-30 points)
      if (latency !== null) {
        if (latency < 50) qualityScore += 30;
        else if (latency < 100) qualityScore += 25;
        else if (latency < 200) qualityScore += 20;
        else if (latency < 500) qualityScore += 15;
        else qualityScore += 10;
      } else {
        qualityScore += 15; // Unknown latency gets average score
      }
      
      // Stability score (0-20 points)
      if (reconnectAttempts === 0) qualityScore += 20;
      else if (reconnectAttempts < 3) qualityScore += 15;
      else if (reconnectAttempts < 5) qualityScore += 10;
      else qualityScore += 5;
      
      // Queue health score (0-10 points)
      if (queuedMessages === 0) qualityScore += 10;
      else if (queuedMessages < 5) qualityScore += 8;
      else if (queuedMessages < 10) qualityScore += 6;
      else qualityScore += 3;
    }

    // Determine quality level
    let qualityLevel: 'excellent' | 'good' | 'fair' | 'poor' | 'offline';
    if (!isConnected) {
      qualityLevel = 'offline';
    } else if (qualityScore >= 90) {
      qualityLevel = 'excellent';
    } else if (qualityScore >= 75) {
      qualityLevel = 'good';
    } else if (qualityScore >= 60) {
      qualityLevel = 'fair';
    } else {
      qualityLevel = 'poor';
    }

    return {
      score: qualityScore,
      level: qualityLevel,
      latency,
      isStable: reconnectAttempts < 3,
      hasQueueBacklog: queuedMessages > 0,
      uptime: uptime || 0
    };
  }, [connectionState]);
}

/**
 * Hook for connection metrics over time
 */
export function useConnectionMetrics(): ConnectionMetrics {
  const networkStatus = useNetworkStatus();
  const healthStatus = serviceIntegration.getHealthStatus();

  return useMemo(() => {
    const now = Date.now();
    const uptime = healthStatus.metrics.uptime ? now - healthStatus.metrics.uptime : null;
    
    // Calculate average latency across all connections
    const connections = Object.values(networkStatus.rooms);
    const latencies = connections
      .map(conn => conn.latency)
      .filter((lat): lat is number => lat !== null);
    const averageLatency = latencies.length > 0 
      ? latencies.reduce((sum, lat) => sum + lat, 0) / latencies.length 
      : null;

    // Calculate message rate (messages per minute)
    const totalMessages = connections.reduce(
      (sum, conn) => sum + (conn.messagesSent || 0) + (conn.messagesReceived || 0), 
      0
    );
    const messageRate = uptime ? (totalMessages / (uptime / 60000)) : 0; // per minute

    return {
      totalConnections: networkStatus.activeConnections,
      uptime,
      averageLatency,
      messageRate,
      errorRate: healthStatus.metrics.totalErrors / Math.max(1, healthStatus.metrics.totalErrors + healthStatus.metrics.successfulRecoveries),
      reconnectionRate: healthStatus.metrics.recoveryAttempts / Math.max(1, healthStatus.metrics.totalErrors)
    };
  }, [networkStatus, healthStatus]);
}

/**
 * Hook for real-time connection events
 */
export function useConnectionEvents(
  onConnected?: (roomId: string) => void,
  onDisconnected?: (roomId: string, reason?: string) => void,
  onReconnecting?: (roomId: string, attempt: number) => void,
  onError?: (roomId: string, error: string) => void
) {
  useEffect(() => {
    const handleConnected = (event: Event) => {
      const customEvent = event as CustomEvent;
      const { roomId } = customEvent.detail;
      onConnected?.(roomId);
    };

    const handleDisconnected = (event: Event) => {
      const customEvent = event as CustomEvent;
      const { roomId, reason } = customEvent.detail;
      onDisconnected?.(roomId, reason);
    };

    const handleReconnecting = (event: Event) => {
      const customEvent = event as CustomEvent;
      const { roomId, attempt } = customEvent.detail;
      onReconnecting?.(roomId, attempt);
    };

    const handleError = (event: Event) => {
      const customEvent = event as CustomEvent;
      const { roomId, error } = customEvent.detail;
      onError?.(roomId, error);
    };

    // Add event listeners
    if (onConnected) networkService.addEventListener('connected', handleConnected);
    if (onDisconnected) networkService.addEventListener('disconnected', handleDisconnected);
    if (onReconnecting) networkService.addEventListener('reconnecting', handleReconnecting);
    if (onError) networkService.addEventListener('connectionError', handleError);

    return () => {
      // Cleanup
      if (onConnected) networkService.removeEventListener('connected', handleConnected);
      if (onDisconnected) networkService.removeEventListener('disconnected', handleDisconnected);
      if (onReconnecting) networkService.removeEventListener('reconnecting', handleReconnecting);
      if (onError) networkService.removeEventListener('connectionError', handleError);
    };
  }, [onConnected, onDisconnected, onReconnecting, onError]);
}

// Helper functions
function getInitialConnectionState(roomId?: string): ConnectionState {
  const networkStatus = networkService.getStatus();
  const roomStatus = roomId ? networkStatus.rooms[roomId] : null;

  return {
    isConnected: roomStatus ? roomStatus.connected : false,
    isConnecting: false,
    isReconnecting: false,
    roomId: roomStatus?.roomId || null,
    connectedAt: roomStatus?.connectedAt || null,
    uptime: roomStatus?.uptime || null,
    latency: roomStatus?.latency || null,
    messagesSent: roomStatus?.messagesSent || 0,
    messagesReceived: roomStatus?.messagesReceived || 0,
    queuedMessages: roomStatus?.queueSize || 0,
    status: roomStatus?.connected ? 'connected' : 'disconnected',
    error: null,
    reconnectAttempts: roomStatus?.reconnectAttempts || 0,
    lastActivity: roomStatus?.lastActivity || null
  };
}

function determineConnectionStatus(
  roomStatus: ConnectionStatus | null,
  overallHealthy: boolean
): ConnectionState['status'] {
  if (!roomStatus) {
    return overallHealthy ? 'disconnected' : 'error';
  }

  if (roomStatus.reconnecting) return 'reconnecting';
  if (roomStatus.connected) return 'connected';
  if (roomStatus.status === 'connecting') return 'connecting';
  
  return 'disconnected';
}

export default useConnectionStatus;