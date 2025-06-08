// ===== frontend/network/core/EventEmitter.js =====
/**
 * Simple event emitter for internal communication
 * Single Responsibility: Event pub/sub
 */
export class EventEmitter {
    constructor() {
        this.events = new Map();
    }

    on(event, callback) {
        if (!this.events.has(event)) {
            this.events.set(event, new Set());
        }
        this.events.get(event).add(callback);
        
        // Return unsubscribe function
        return () => this.off(event, callback);
    }

    off(event, callback) {
        if (this.events.has(event)) {
            if (callback) {
                this.events.get(event).delete(callback);
            } else {
                // Remove all listeners for this event
                this.events.delete(event);
            }
        }
    }

    emit(event, data) {
        if (this.events.has(event)) {
            const callbacks = this.events.get(event);
            callbacks.forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in event listener for ${event}:`, error);
                }
            });
        }
    }

    clear() {
        this.events.clear();
    }
}