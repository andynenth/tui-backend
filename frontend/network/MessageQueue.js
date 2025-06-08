// ===== frontend/network/MessageQueue.js =====
/**
 * Message queue for offline/reconnection scenarios
 * Single Responsibility: Queue messages when disconnected
 */
export class MessageQueue {
    constructor(maxSize = 100) {
        this.queue = [];
        this.maxSize = maxSize;
    }

    enqueue(message) {
        if (this.queue.length >= this.maxSize) {
            // Remove oldest message if queue is full
            this.queue.shift();
        }
        
        this.queue.push({
            ...message,
            timestamp: Date.now(),
            attempts: 0
        });
    }

    dequeue() {
        return this.queue.shift();
    }

    peek() {
        return this.queue[0];
    }

    size() {
        return this.queue.length;
    }

    clear() {
        this.queue = [];
    }

    getAll() {
        return [...this.queue];
    }

    // Remove messages older than specified age (in milliseconds)
    pruneOldMessages(maxAge = 60000) {
        const cutoff = Date.now() - maxAge;
        this.queue = this.queue.filter(msg => msg.timestamp > cutoff);
    }
}