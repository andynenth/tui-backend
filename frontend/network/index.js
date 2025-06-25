// ===== frontend/network/index.js =====
/**
 * Main export file for the network module
 * Provides new modular API
 */

// New modular API
export { SocketManager } from './SocketManager.js';
export { ConnectionMonitor } from './ConnectionMonitor.js';
export { MessageQueue } from './MessageQueue.js';
export { ReconnectionManager } from './ReconnectionManager.js';