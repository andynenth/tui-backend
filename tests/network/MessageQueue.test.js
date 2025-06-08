// ===== tests/network/MessageQueue.test.js =====
import { MessageQueue } from '../../frontend/network/MessageQueue.js';

describe('MessageQueue', () => {
  let queue;
  
  beforeEach(() => {
    queue = new MessageQueue(5); // Small size for testing
  });
  
  test('should enqueue and dequeue messages', () => {
    queue.enqueue({ event: 'test1', data: {} });
    queue.enqueue({ event: 'test2', data: {} });
    
    expect(queue.size()).toBe(2);
    
    const msg1 = queue.dequeue();
    expect(msg1.event).toBe('test1');
    expect(queue.size()).toBe(1);
  });
  
  test('should respect max size', () => {
    for (let i = 0; i < 10; i++) {
      queue.enqueue({ event: `test${i}`, data: {} });
    }
    
    expect(queue.size()).toBe(5);
    
    const first = queue.dequeue();
    expect(first.event).toBe('test5'); // First 5 were dropped
  });
  
  test('should prune old messages', () => {
    const oldMsg = { event: 'old', data: {} };
    oldMsg.timestamp = Date.now() - 70000; // 70 seconds old
    
    // Manually add old message
    queue.queue.push(oldMsg);
    queue.enqueue({ event: 'new', data: {} });
    
    expect(queue.size()).toBe(2);
    
    queue.pruneOldMessages(60000); // Remove messages older than 60 seconds
    
    expect(queue.size()).toBe(1);
    expect(queue.peek().event).toBe('new');
  });
});