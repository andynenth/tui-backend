// frontend/components/ConnectionStatus.js

import { Container, Text, TextStyle, Graphics } from 'pixi.js';
import { SocketManager } from '../network/SocketManager.js';

/**
 * ConnectionStatus component displays real-time connection information
 * 
 * REFACTORED: Enhanced to show more detailed status from new SocketManager
 * Can be used standalone or with a provided SocketManager instance
 */
export class ConnectionStatus {
    constructor(socketManager = null) {
        // Use provided SocketManager or create a reference
        this.socketManager = socketManager;
        
        // Create UI container
        this.view = new Container();
        this.view.layout = {
            flexDirection: 'row',
            alignItems: 'center',
            gap: 8,
        };

        // Status indicator (colored circle)
        this.statusIndicator = new Graphics();
        this._updateIndicator('disconnected');

        // Status text
        this.statusText = new Text({
            text: '🔴 Disconnected',
            style: new TextStyle({
                fontFamily: 'Arial',
                fontSize: 14,
                fill: '#ffffff',
            }),
        });

        // Additional info text (latency, queue size, etc.)
        this.infoText = new Text({
            text: '',
            style: new TextStyle({
                fontFamily: 'Arial',
                fontSize: 12,
                fill: '#999999',
            }),
        });

        // Add components to view
        this.view.addChild(this.statusIndicator, this.statusText, this.infoText);

        // Set up event listeners if SocketManager provided
        if (this.socketManager) {
            this._setupEventListeners();
            this._updateFromSocketManager();
        }


        // Update periodically to show real-time stats
        this._startPeriodicUpdate();
    }

    /**
     * Set up event listeners for the SocketManager
     */
    _setupEventListeners() {
        if (!this.socketManager) return;

        // Connection events
        this.socketManager.on('connected', (data) => {
            this._updateStatus('connected', '🟢 Connected');
            if (data.roomId) {
                this.infoText.text = `Room: ${data.roomId}`;
            }
        });

        this.socketManager.on('disconnected', (data) => {
            this._updateStatus('disconnected', '🔴 Disconnected');
            this.infoText.text = '';
        });

        this.socketManager.on('reconnecting', (status) => {
            const text = `🟡 Reconnecting... (${status.attempts}/${status.maxAttempts})`;
            this._updateStatus('reconnecting', text);
            
            // Show additional info
            if (status.isReconnecting) {
                this.infoText.text = 'Auto-reconnect enabled';
            }
        });

        this.socketManager.on('reconnected', () => {
            this._updateStatus('connected', '🟢 Reconnected');
        });

        this.socketManager.on('connection_failed', (data) => {
            this._updateStatus('failed', '❌ Connection Failed');
            if (data.error) {
                this.infoText.text = 'Check network connection';
            }
        });

        // Message events
        this.socketManager.on('message_queued', () => {
            this._updateQueueInfo();
        });

        this.socketManager.on('message_sent', () => {
            this._updateQueueInfo();
        });
    }

    /**
     * Update status from current SocketManager state
     */
    _updateFromSocketManager() {
        if (!this.socketManager) return;

        const status = this.socketManager.getStatus();
        
        if (status.connected) {
            this._updateStatus('connected', '🟢 Connected');
            
            // Show additional info
            const info = [];
            if (status.roomId) {
                info.push(`Room: ${status.roomId}`);
            }
            if (status.latency) {
                info.push(`${status.latency}ms`);
            }
            if (status.queueSize > 0) {
                info.push(`Queue: ${status.queueSize}`);
            }
            this.infoText.text = info.join(' | ');
            
        } else if (status.status === 'reconnecting') {
            const reconnectInfo = status.reconnection;
            const text = `🟡 Reconnecting... (${reconnectInfo.attempts}/${reconnectInfo.maxAttempts})`;
            this._updateStatus('reconnecting', text);
            
        } else {
            this._updateStatus('disconnected', '🔴 Disconnected');
            this.infoText.text = '';
        }
    }

    /**
     * Update queue information display
     */
    _updateQueueInfo() {
        if (!this.socketManager) return;

        const status = this.socketManager.getStatus();
        if (status.queueSize > 0) {
            // Add queue size to info if not already showing
            const currentInfo = this.infoText.text;
            if (!currentInfo.includes('Queue:')) {
                this.infoText.text += ` | Queue: ${status.queueSize}`;
            } else {
                // Update queue size
                this.infoText.text = this.infoText.text.replace(
                    /Queue: \d+/,
                    `Queue: ${status.queueSize}`
                );
            }
        }
    }

    /**
     * Update the visual status
     */
    _updateStatus(state, text) {
        this.statusText.text = text;
        this._updateIndicator(state);
        
        // Update text color based on state
        switch (state) {
            case 'connected':
                this.statusText.style.fill = '#00ff00';
                break;
            case 'reconnecting':
                this.statusText.style.fill = '#ffaa00';
                break;
            case 'disconnected':
            case 'failed':
                this.statusText.style.fill = '#ff0000';
                break;
        }
    }

    /**
     * Update the colored indicator
     */
    _updateIndicator(state) {
        this.statusIndicator.clear();
        
        let color;
        switch (state) {
            case 'connected':
                color = 0x00ff00; // Green
                break;
            case 'reconnecting':
                color = 0xffaa00; // Orange
                break;
            case 'disconnected':
            case 'failed':
                color = 0xff0000; // Red
                break;
            default:
                color = 0x666666; // Gray
        }
        
        // Draw circle indicator using PixiJS v8 API
        this.statusIndicator.circle(0, 0, 6);
        this.statusIndicator.fill(color);
        
    }


    /**
     * Start periodic updates for real-time stats
     */
    _startPeriodicUpdate() {
        this._updateInterval = setInterval(() => {
            if (this.socketManager) {
                this._updateFromSocketManager();
            }
        }, 1000); // Update every second
    }

    /**
     * Clean up resources
     */
    destroy() {
        // Clear update interval
        if (this._updateInterval) {
            clearInterval(this._updateInterval);
            this._updateInterval = null;
        }

        // Remove from parent if exists
        if (this.view.parent) {
            this.view.parent.removeChild(this.view);
        }

        // Clean up PixiJS resources
        this.statusIndicator.destroy();
        this.statusText.destroy();
        this.infoText.destroy();
        this.view.destroy();

        // Clear references
        this.socketManager = null;
    }

    /**
     * Static method to create a standalone connection monitor
     */
    static createStandalone() {
        return new ConnectionStatus();
    }

    /**
     * Attach to an existing SocketManager
     */
    attachToSocketManager(socketManager) {
        this.socketManager = socketManager;
        this._setupEventListeners();
        this._updateFromSocketManager();
    }
}