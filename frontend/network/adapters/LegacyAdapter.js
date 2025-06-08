// ===== frontend/network/adapters/LegacyAdapter.js =====
/**
 * Adapter to maintain backward compatibility with old socketManager API
 * This allows gradual migration without breaking existing code
 */
import { SocketManager } from '../SocketManager.js';

// Global instance for backward compatibility
let globalSocketManager = null;

// Legacy API functions
export function connect(roomId) {
    if (!globalSocketManager) {
        globalSocketManager = new SocketManager();
    }
    return globalSocketManager.connect(roomId);
}

export function disconnect() {
    if (globalSocketManager) {
        globalSocketManager.disconnect();
        globalSocketManager = null;
    }
}

export function emit(event, data) {
    if (globalSocketManager) {
        globalSocketManager.send(event, data);
    } else {
        console.warn('Socket not connected. Cannot emit:', event);
    }
}

export function on(event, callback) {
    if (!globalSocketManager) {
        globalSocketManager = new SocketManager();
    }
    return globalSocketManager.on(event, callback);
}

export function off(event, callback) {
    if (globalSocketManager) {
        globalSocketManager.off(event, callback);
    }
}

export function getSocketReadyState() {
    if (!globalSocketManager) {
        return { state: null, text: "No connection" };
    }
    
    const status = globalSocketManager.getStatus();
    const stateMap = {
        'connected': { state: WebSocket.OPEN, text: 'Connected' },
        'connecting': { state: WebSocket.CONNECTING, text: 'Connecting' },
        'disconnected': { state: WebSocket.CLOSED, text: 'Disconnected' },
        'reconnecting': { state: WebSocket.CONNECTING, text: 'Reconnecting' }
    };
    
    return stateMap[status.status] || { state: WebSocket.CLOSED, text: 'Unknown' };
}

export function getConnectionStatus() {
    if (!globalSocketManager) {
        return {
            readyState: WebSocket.CLOSED,
            isConnected: false,
            reconnectAttempts: 0,
            maxReconnectAttempts: 0,
            currentRoom: null
        };
    }
    
    const status = globalSocketManager.getStatus();
    return {
        readyState: status.connected ? WebSocket.OPEN : WebSocket.CLOSED,
        isConnected: status.connected,
        reconnectAttempts: status.reconnection.attempts,
        maxReconnectAttempts: status.reconnection.maxAttempts,
        currentRoom: status.roomId
    };
}