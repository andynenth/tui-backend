/**
 * WebSocket Mock for Testing
 *
 * Provides a mock implementation of WebSocket for testing NetworkService
 * and GameService without requiring actual WebSocket connections.
 */

export class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  constructor(url) {
    this.url = url;
    this.readyState = MockWebSocket.CONNECTING;
    this.protocol = '';
    this.extensions = '';
    this.binaryType = 'blob';

    // Event handlers
    this.onopen = null;
    this.onclose = null;
    this.onmessage = null;
    this.onerror = null;

    // For testing purposes
    this.sentMessages = [];
    this.mockLatency = 0;

    // Simulate connection after next tick
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      if (this.onopen) {
        this.onopen({ target: this });
      }
    }, this.mockLatency);
  }

  send(data) {
    if (this.readyState !== MockWebSocket.OPEN) {
      throw new Error('WebSocket is not open');
    }

    this.sentMessages.push(data);

    // Echo back pong for ping messages (for heartbeat testing)
    try {
      const message = JSON.parse(data);
      if (message.event === 'ping') {
        setTimeout(() => {
          this.mockReceive({
            event: 'pong',
            data: { timestamp: message.data.timestamp },
          });
        }, 10);
      }
    } catch (e) {
      // Not JSON, ignore
    }
  }

  close(code = 1000, reason = '') {
    this.readyState = MockWebSocket.CLOSING;
    setTimeout(() => {
      this.readyState = MockWebSocket.CLOSED;
      if (this.onclose) {
        this.onclose({
          target: this,
          code,
          reason,
          wasClean: code === 1000,
        });
      }
    }, 10);
  }

  // Test helpers
  mockReceive(data) {
    if (this.readyState === MockWebSocket.OPEN && this.onmessage) {
      const messageData =
        typeof data === 'string' ? data : JSON.stringify(data);
      this.onmessage({
        target: this,
        data: messageData,
      });
    }
  }

  mockError(error = 'Mock error') {
    if (this.onerror) {
      this.onerror({
        target: this,
        error: new Error(error),
      });
    }
  }

  mockDisconnect(code = 1006, reason = 'Connection lost') {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose({
        target: this,
        code,
        reason,
        wasClean: false,
      });
    }
  }

  // Mock methods for testing
  getSentMessages() {
    return this.sentMessages.slice();
  }

  clearSentMessages() {
    this.sentMessages = [];
  }

  setMockLatency(ms) {
    this.mockLatency = ms;
  }
}

// Replace global WebSocket with mock
global.WebSocket = MockWebSocket;

export default MockWebSocket;
