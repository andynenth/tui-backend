// ===== frontend/network/core/SocketConnection.js =====
/**
 * Core WebSocket connection wrapper
 * Single Responsibility: Manage a single WebSocket connection
 */
export class SocketConnection {
  constructor(url) {
    this.url = url;
    this.socket = null;
    this.readyState = WebSocket.CLOSED;
  }

  async connect() {
    return new Promise((resolve, reject) => {
      console.log(`🔌 [SocketConnection] Connecting to: ${this.url}`);
      try {
        this.socket = new WebSocket(this.url);

        this.socket.onopen = () => {
          console.log("✅ [SocketConnection] WebSocket opened");
          this.readyState = WebSocket.OPEN;
          resolve(this.socket);
        };

        this.socket.onerror = (error) => {
          this.readyState = WebSocket.CLOSED;
          reject(error);
        };

        // Set a connection timeout
        setTimeout(() => {
          if (this.readyState !== WebSocket.OPEN) {
            this.socket.close();
            reject(new Error("Connection timeout"));
          }
        }, 5000);
      } catch (error) {
        reject(error);
      }
    });
  }

  send(data) {
    if (this.isConnected()) {
      this.socket.send(JSON.stringify(data));
      return true;
    }
    return false;
  }

  close() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
      this.readyState = WebSocket.CLOSED;
    }
  }

  isConnected() {
    return this.socket && this.socket.readyState === WebSocket.OPEN;
  }

  onMessage(callback) {
    if (this.socket) {
      this.socket.onmessage = (event) => {
        console.log("📨 [SocketConnection] Raw WS message event:", event);
        console.log(
          "📦 [SocketConnection] Message data type:",
          typeof event.data
        );
        if (this.messageHandler) {
          let data = event.data;

          // Parse if string
          if (typeof data === "string") {
            try {
              data = JSON.parse(data);
            } catch (e) {
              console.error("Failed to parse WebSocket message:", e);
              return;
            }
          }

          this.messageHandler(data);
        }
        try {
          const data = JSON.parse(event.data);
          callback(data);
        } catch (error) {
          console.error("Failed to parse message:", error);
        }
      };
    }
  }

  onClose(callback) {
    if (this.socket) {
      this.socket.onclose = callback;
    }
  }

  onError(callback) {
    if (this.socket) {
      this.socket.onerror = callback;
    }
  }
}
