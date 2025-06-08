// ===== frontend/network/ConnectionMonitor.js =====
/**
 * Monitor connection health and statistics
 * Single Responsibility: Track connection status and metrics
 */
export class ConnectionMonitor {
    constructor() {
        this.status = 'disconnected';
        this.lastConnectedAt = null;
        this.lastDisconnectedAt = null;
        this.connectionAttempts = 0;
        this.messagesSent = 0;
        this.messagesReceived = 0;
        this.lastError = null;
        this.pingInterval = null;
        this.lastPingTime = null;
        this.latency = null;
    }

    markConnected() {
        this.status = 'connected';
        this.lastConnectedAt = Date.now();
        this.connectionAttempts = 0;
        this.lastError = null;
    }

    markDisconnected(error = null) {
        this.status = 'disconnected';
        this.lastDisconnectedAt = Date.now();
        if (error) {
            this.lastError = error;
        }
        this.stopPingMonitoring();
    }

    markReconnecting() {
        this.status = 'reconnecting';
        this.connectionAttempts++;
    }

    recordMessageSent() {
        this.messagesSent++;
    }

    recordMessageReceived() {
        this.messagesReceived++;
    }

    startPingMonitoring(connection, interval = 30000) {
        this.stopPingMonitoring();
        
        this.pingInterval = setInterval(() => {
            if (connection.isConnected()) {
                const pingTime = Date.now();
                connection.send({ event: 'ping', data: { timestamp: pingTime } });
                this.lastPingTime = pingTime;
            }
        }, interval);
    }

    stopPingMonitoring() {
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
            this.pingInterval = null;
        }
    }

    recordPong(timestamp) {
        if (this.lastPingTime) {
            this.latency = Date.now() - this.lastPingTime;
        }
    }

    getStatus() {
        return {
            status: this.status,
            connected: this.status === 'connected',
            lastConnectedAt: this.lastConnectedAt,
            lastDisconnectedAt: this.lastDisconnectedAt,
            connectionAttempts: this.connectionAttempts,
            uptime: this.lastConnectedAt ? Date.now() - this.lastConnectedAt : 0,
            messagesSent: this.messagesSent,
            messagesReceived: this.messagesReceived,
            latency: this.latency,
            lastError: this.lastError
        };
    }

    reset() {
        this.status = 'disconnected';
        this.lastConnectedAt = null;
        this.lastDisconnectedAt = null;
        this.connectionAttempts = 0;
        this.messagesSent = 0;
        this.messagesReceived = 0;
        this.lastError = null;
        this.latency = null;
        this.stopPingMonitoring();
    }
}