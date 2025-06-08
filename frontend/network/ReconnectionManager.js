// ===== frontend/network/ReconnectionManager.js =====
/**
 * Handle reconnection logic with exponential backoff
 * Single Responsibility: Manage reconnection attempts
 */
export class ReconnectionManager {
    constructor(options = {}) {
        this.maxAttempts = options.maxAttempts || 5;
        this.baseDelay = options.baseDelay || 1000;
        this.maxDelay = options.maxDelay || 30000;
        this.factor = options.factor || 2;
        
        this.attempts = 0;
        this.isReconnecting = false;
        this.reconnectTimer = null;
        this.abortController = null;
    }

    async scheduleReconnect(connectFunction) {
        if (this.isReconnecting) {
            return null;
        }

        this.isReconnecting = true;
        this.abortController = new AbortController();

        const attemptReconnect = async () => {
            if (this.attempts >= this.maxAttempts || this.abortController.signal.aborted) {
                this.stop();
                throw new Error('Max reconnection attempts reached');
            }

            const delay = this.calculateDelay();
            console.log(`Reconnection attempt ${this.attempts + 1}/${this.maxAttempts} in ${delay}ms`);

            await new Promise(resolve => {
                this.reconnectTimer = setTimeout(resolve, delay);
            });

            if (this.abortController.signal.aborted) {
                return null;
            }

            this.attempts++;

            try {
                const result = await connectFunction();
                this.reset(); // Success - reset everything
                return result;
            } catch (error) {
                console.error(`Reconnection attempt ${this.attempts} failed:`, error);
                
                if (this.attempts < this.maxAttempts && !this.abortController.signal.aborted) {
                    return attemptReconnect(); // Recursive retry
                } else {
                    this.stop();
                    throw error;
                }
            }
        };

        return attemptReconnect();
    }

    calculateDelay() {
        const delay = Math.min(
            this.baseDelay * Math.pow(this.factor, this.attempts),
            this.maxDelay
        );
        
        // Add jitter (±10%)
        const jitter = delay * 0.1;
        return delay + (Math.random() * 2 - 1) * jitter;
    }

    stop() {
        this.isReconnecting = false;
        
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
        
        if (this.abortController) {
            this.abortController.abort();
            this.abortController = null;
        }
    }

    reset() {
        this.attempts = 0;
        this.stop();
    }

    getStatus() {
        return {
            isReconnecting: this.isReconnecting,
            attempts: this.attempts,
            maxAttempts: this.maxAttempts,
            canRetry: this.attempts < this.maxAttempts
        };
    }
}