// ===== CONNECTION STATUS COMPONENT =====
// frontend/components/ConnectionStatus.js - ไฟล์ใหม่

import { Container, Text, TextStyle } from 'pixi.js';
import { getConnectionStatus, on as onSocketEvent, off as offSocketEvent } from '../socketManager.js';

export class ConnectionStatus {
    constructor() {
        this.view = new Container();
        this.view.layout = {
            position: 'absolute',
            top: 10,
            right: 10,
            padding: 8,
        };

        this.statusText = new Text({
            text: '🔴 Disconnected',
            style: new TextStyle({
                fontFamily: 'Arial',
                fontSize: 14,
                fill: '#ffffff',
            }),
        });

        this.view.addChild(this.statusText);
        this.setupEventListeners();
        this.updateStatus();
    }

    setupEventListeners() {
        this.handleConnected = () => {
            this.statusText.text = '🟢 Connected';
            this.statusText.style.fill = '#00ff00';
        };

        this.handleDisconnected = () => {
            this.statusText.text = '🔴 Disconnected';
            this.statusText.style.fill = '#ff0000';
        };

        this.handleReconnecting = (data) => {
            this.statusText.text = `🟡 Reconnecting... (${data.attempt}/${data.maxAttempts})`;
            this.statusText.style.fill = '#ffaa00';
        };

        this.handleConnectionFailed = () => {
            this.statusText.text = '❌ Connection Failed';
            this.statusText.style.fill = '#ff0000';
        };

        onSocketEvent('connected', this.handleConnected);
        onSocketEvent('disconnected', this.handleDisconnected);
        onSocketEvent('reconnecting', this.handleReconnecting);
        onSocketEvent('connection_failed', this.handleConnectionFailed);
    }

    updateStatus() {
        const status = getConnectionStatus();
        if (status.isConnected) {
            this.handleConnected();
        } else {
            this.handleDisconnected();
        }
    }

    destroy() {
        offSocketEvent('connected', this.handleConnected);
        offSocketEvent('disconnected', this.handleDisconnected);
        offSocketEvent('reconnecting', this.handleReconnecting);
        offSocketEvent('connection_failed', this.handleConnectionFailed);
    }
}