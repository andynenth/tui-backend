// ===== frontend/network/index.js =====
/**
 * Main export file for the network module
 * Provides both new API and legacy compatibility
 */

// New modular API
export { SocketManager } from './SocketManager.js';
export { ConnectionMonitor } from './ConnectionMonitor.js';
export { MessageQueue } from './MessageQueue.js';
export { ReconnectionManager } from './ReconnectionManager.js';

// Legacy API for backward compatibility
export {
    connect,
    disconnect,
    emit,
    on,
    off,
    getSocketReadyState,
    getConnectionStatus
} from './adapters/LegacyAdapter.js';