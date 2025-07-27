"""
In-memory message queue implementations.

Provides high-performance message queues for development and testing.
"""

import asyncio
import heapq
from typing import Dict, Optional, List, Set, Any, Tuple
from datetime import datetime, timedelta
from collections import deque
import logging

from .base import (
    Message,
    MessagePriority,
    MessageStatus,
    IMessageQueue,
    DeliveryOptions,
    T
)


logger = logging.getLogger(__name__)


class InMemoryQueue(IMessageQueue[T]):
    """
    Simple in-memory FIFO queue.
    
    Features:
    - FIFO ordering
    - Message acknowledgment
    - TTL support
    - Async operations
    """
    
    def __init__(self, name: str = "default"):
        """Initialize in-memory queue."""
        self.name = name
        self._queue: deque[Message[T]] = deque()
        self._messages: Dict[str, Message[T]] = {}
        self._processing: Set[str] = set()
        self._lock = asyncio.Lock()
        self._not_empty = asyncio.Condition(self._lock)
        self._stats = {
            'enqueued': 0,
            'dequeued': 0,
            'acknowledged': 0,
            'rejected': 0,
            'expired': 0
        }
    
    async def enqueue(
        self,
        message: Message[T],
        options: Optional[DeliveryOptions] = None
    ) -> str:
        """Add message to queue."""
        async with self._lock:
            # Apply delivery options
            if options:
                if options.ttl:
                    message.metadata.expires_at = datetime.utcnow() + options.ttl
                if options.priority != MessagePriority.NORMAL:
                    message.priority = options.priority
                if options.correlation_id:
                    message.metadata.correlation_id = options.correlation_id
            
            # Store message
            message_id = message.metadata.message_id
            self._messages[message_id] = message
            
            # Handle delay
            if options and options.delay:
                asyncio.create_task(self._delayed_enqueue(message, options.delay))
            else:
                self._queue.append(message)
                self._not_empty.notify()
            
            self._stats['enqueued'] += 1
            
            logger.debug(f"Enqueued message {message_id} to queue {self.name}")
            return message_id
    
    async def dequeue(self, timeout: Optional[float] = None) -> Optional[Message[T]]:
        """Remove and return message from queue."""
        async with self._not_empty:
            # Wait for messages with timeout
            if timeout is not None:
                try:
                    await asyncio.wait_for(
                        self._wait_for_message(),
                        timeout=timeout
                    )
                except asyncio.TimeoutError:
                    return None
            elif len(self._queue) == 0:
                return None
            
            # Find next non-expired message
            while self._queue:
                message = self._queue.popleft()
                
                # Check expiration
                if message.is_expired():
                    self._stats['expired'] += 1
                    message.status = MessageStatus.EXPIRED
                    continue
                
                # Mark as processing
                message.status = MessageStatus.PROCESSING
                self._processing.add(message.metadata.message_id)
                self._stats['dequeued'] += 1
                
                return message
            
            return None
    
    async def peek(self, count: int = 1) -> List[Message[T]]:
        """Peek at messages without removing."""
        async with self._lock:
            messages = []
            
            for message in self._queue:
                if not message.is_expired():
                    messages.append(message)
                    if len(messages) >= count:
                        break
            
            return messages
    
    async def acknowledge(self, message_id: str) -> bool:
        """Acknowledge message processing."""
        async with self._lock:
            if message_id in self._processing:
                self._processing.remove(message_id)
                
                if message_id in self._messages:
                    self._messages[message_id].status = MessageStatus.COMPLETED
                    self._stats['acknowledged'] += 1
                    
                    # Clean up completed message
                    del self._messages[message_id]
                    
                    return True
            
            return False
    
    async def reject(self, message_id: str, requeue: bool = False) -> bool:
        """Reject message."""
        async with self._lock:
            if message_id in self._processing:
                self._processing.remove(message_id)
                
                if message_id in self._messages:
                    message = self._messages[message_id]
                    message.metadata.attempts += 1
                    
                    if requeue:
                        message.status = MessageStatus.PENDING
                        self._queue.append(message)
                        self._not_empty.notify()
                    else:
                        message.status = MessageStatus.FAILED
                        del self._messages[message_id]
                    
                    self._stats['rejected'] += 1
                    return True
            
            return False
    
    async def size(self) -> int:
        """Get queue size."""
        async with self._lock:
            return len(self._queue)
    
    async def clear(self) -> int:
        """Clear all messages."""
        async with self._lock:
            count = len(self._queue)
            self._queue.clear()
            self._messages.clear()
            self._processing.clear()
            return count
    
    async def _wait_for_message(self) -> None:
        """Wait for message to be available."""
        while len(self._queue) == 0:
            await self._not_empty.wait()
    
    async def _delayed_enqueue(self, message: Message[T], delay: timedelta) -> None:
        """Enqueue message after delay."""
        await asyncio.sleep(delay.total_seconds())
        
        async with self._lock:
            self._queue.append(message)
            self._not_empty.notify()
    
    def get_stats(self) -> Dict[str, int]:
        """Get queue statistics."""
        return self._stats.copy()


class PriorityInMemoryQueue(IMessageQueue[T]):
    """
    Priority-based in-memory queue.
    
    Features:
    - Priority ordering
    - Stable FIFO within priority
    - All features of InMemoryQueue
    """
    
    def __init__(self, name: str = "priority"):
        """Initialize priority queue."""
        self.name = name
        self._heap: List[Tuple[int, int, Message[T]]] = []
        self._counter = 0
        self._messages: Dict[str, Message[T]] = {}
        self._processing: Set[str] = set()
        self._lock = asyncio.Lock()
        self._not_empty = asyncio.Condition(self._lock)
        self._stats = {
            'enqueued': 0,
            'dequeued': 0,
            'acknowledged': 0,
            'rejected': 0,
            'expired': 0
        }
    
    async def enqueue(
        self,
        message: Message[T],
        options: Optional[DeliveryOptions] = None
    ) -> str:
        """Add message to priority queue."""
        async with self._lock:
            # Apply delivery options
            if options:
                if options.ttl:
                    message.metadata.expires_at = datetime.utcnow() + options.ttl
                if options.priority != MessagePriority.NORMAL:
                    message.priority = options.priority
                if options.correlation_id:
                    message.metadata.correlation_id = options.correlation_id
            
            # Store message
            message_id = message.metadata.message_id
            self._messages[message_id] = message
            
            # Handle delay
            if options and options.delay:
                asyncio.create_task(self._delayed_enqueue(message, options.delay))
            else:
                # Add to heap with negative priority for max-heap behavior
                self._counter += 1
                heapq.heappush(
                    self._heap,
                    (-message.priority.value, self._counter, message)
                )
                self._not_empty.notify()
            
            self._stats['enqueued'] += 1
            
            logger.debug(
                f"Enqueued message {message_id} with priority {message.priority.name} "
                f"to queue {self.name}"
            )
            return message_id
    
    async def dequeue(self, timeout: Optional[float] = None) -> Optional[Message[T]]:
        """Remove and return highest priority message."""
        async with self._not_empty:
            # Wait for messages with timeout
            if timeout is not None:
                try:
                    await asyncio.wait_for(
                        self._wait_for_message(),
                        timeout=timeout
                    )
                except asyncio.TimeoutError:
                    return None
            elif len(self._heap) == 0:
                return None
            
            # Find next non-expired message
            while self._heap:
                _, _, message = heapq.heappop(self._heap)
                
                # Check expiration
                if message.is_expired():
                    self._stats['expired'] += 1
                    message.status = MessageStatus.EXPIRED
                    continue
                
                # Mark as processing
                message.status = MessageStatus.PROCESSING
                self._processing.add(message.metadata.message_id)
                self._stats['dequeued'] += 1
                
                return message
            
            return None
    
    async def peek(self, count: int = 1) -> List[Message[T]]:
        """Peek at highest priority messages."""
        async with self._lock:
            messages = []
            temp_heap = self._heap.copy()
            
            while temp_heap and len(messages) < count:
                _, _, message = heapq.heappop(temp_heap)
                if not message.is_expired():
                    messages.append(message)
            
            return messages
    
    async def acknowledge(self, message_id: str) -> bool:
        """Acknowledge message processing."""
        async with self._lock:
            if message_id in self._processing:
                self._processing.remove(message_id)
                
                if message_id in self._messages:
                    self._messages[message_id].status = MessageStatus.COMPLETED
                    self._stats['acknowledged'] += 1
                    
                    # Clean up completed message
                    del self._messages[message_id]
                    
                    return True
            
            return False
    
    async def reject(self, message_id: str, requeue: bool = False) -> bool:
        """Reject message."""
        async with self._lock:
            if message_id in self._processing:
                self._processing.remove(message_id)
                
                if message_id in self._messages:
                    message = self._messages[message_id]
                    message.metadata.attempts += 1
                    
                    if requeue:
                        message.status = MessageStatus.PENDING
                        self._counter += 1
                        heapq.heappush(
                            self._heap,
                            (-message.priority.value, self._counter, message)
                        )
                        self._not_empty.notify()
                    else:
                        message.status = MessageStatus.FAILED
                        del self._messages[message_id]
                    
                    self._stats['rejected'] += 1
                    return True
            
            return False
    
    async def size(self) -> int:
        """Get queue size."""
        async with self._lock:
            return len(self._heap)
    
    async def clear(self) -> int:
        """Clear all messages."""
        async with self._lock:
            count = len(self._heap)
            self._heap.clear()
            self._messages.clear()
            self._processing.clear()
            self._counter = 0
            return count
    
    async def _wait_for_message(self) -> None:
        """Wait for message to be available."""
        while len(self._heap) == 0:
            await self._not_empty.wait()
    
    async def _delayed_enqueue(self, message: Message[T], delay: timedelta) -> None:
        """Enqueue message after delay."""
        await asyncio.sleep(delay.total_seconds())
        
        async with self._lock:
            self._counter += 1
            heapq.heappush(
                self._heap,
                (-message.priority.value, self._counter, message)
            )
            self._not_empty.notify()
    
    def get_stats(self) -> Dict[str, int]:
        """Get queue statistics."""
        return self._stats.copy()


class BoundedInMemoryQueue(InMemoryQueue[T]):
    """
    Bounded in-memory queue with size limits.
    
    Features:
    - Maximum size enforcement
    - Overflow strategies
    - Backpressure support
    """
    
    def __init__(
        self,
        name: str = "bounded",
        max_size: int = 1000,
        overflow_strategy: str = "reject"
    ):
        """
        Initialize bounded queue.
        
        Args:
            name: Queue name
            max_size: Maximum queue size
            overflow_strategy: Strategy when full ('reject', 'drop_oldest', 'block')
        """
        super().__init__(name)
        self.max_size = max_size
        self.overflow_strategy = overflow_strategy
        self._not_full = asyncio.Condition(self._lock)
    
    async def enqueue(
        self,
        message: Message[T],
        options: Optional[DeliveryOptions] = None
    ) -> str:
        """Add message to bounded queue."""
        async with self._lock:
            # Check size limit
            if len(self._queue) >= self.max_size:
                if self.overflow_strategy == "reject":
                    raise OverflowError(f"Queue {self.name} is full")
                elif self.overflow_strategy == "drop_oldest":
                    # Drop oldest message
                    dropped = self._queue.popleft()
                    if dropped.metadata.message_id in self._messages:
                        del self._messages[dropped.metadata.message_id]
                elif self.overflow_strategy == "block":
                    # Wait for space
                    while len(self._queue) >= self.max_size:
                        await self._not_full.wait()
            
            # Enqueue normally
            result = await super().enqueue(message, options)
            
            # Notify if space available
            if len(self._queue) < self.max_size:
                self._not_full.notify()
            
            return result
    
    async def dequeue(self, timeout: Optional[float] = None) -> Optional[Message[T]]:
        """Remove and return message, notify if space available."""
        result = await super().dequeue(timeout)
        
        if result is not None:
            async with self._lock:
                self._not_full.notify()
        
        return result
    
    async def acknowledge(self, message_id: str) -> bool:
        """Acknowledge and notify if space available."""
        result = await super().acknowledge(message_id)
        
        if result:
            async with self._lock:
                self._not_full.notify()
        
        return result