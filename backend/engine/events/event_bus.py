# backend/engine/events/event_bus.py

import asyncio
import logging
from typing import Dict, List, Callable, Any, Optional, Set, Union
from weakref import WeakSet
from datetime import datetime
from dataclasses import dataclass, field

from .event_types import GameEvent, EventType, EventPriority
from .event_handlers import IEventHandler, EventHandlerRegistry
from .event_middleware import IEventMiddleware

logger = logging.getLogger(__name__)


@dataclass
class EventBusMetrics:
    """Metrics tracking for event bus performance."""
    events_published: int = 0
    events_processed: int = 0
    events_failed: int = 0
    average_processing_time: float = 0.0
    handlers_registered: int = 0
    middleware_count: int = 0
    

class EventBus:
    """
    🚀 **Centralized Event Bus** - Phase 4 Event System Unification
    
    High-performance publisher-subscriber event system that replaces direct method calls
    with event-driven architecture for optimal component decoupling.
    
    Features:
    - Async event publishing with priority queues
    - Middleware pipeline for cross-cutting concerns
    - Handler registry with automatic cleanup
    - Event filtering and routing
    - Performance metrics and monitoring
    - Room-scoped event isolation
    """
    
    def __init__(self, room_id: Optional[str] = None):
        self.room_id = room_id
        self.is_running = False
        
        # Event handlers registry
        self.handler_registry = EventHandlerRegistry()
        
        # Event queues by priority
        self.event_queues: Dict[EventPriority, asyncio.Queue] = {
            priority: asyncio.Queue() for priority in EventPriority
        }
        
        # Middleware pipeline
        self.middleware: List[IEventMiddleware] = []
        
        # Processing tasks
        self.processing_tasks: Set[asyncio.Task] = set()
        
        # Event filtering
        self.event_filters: Dict[EventType, List[Callable[[GameEvent], bool]]] = {}
        
        # Metrics tracking
        self.metrics = EventBusMetrics()
        
        # Event history for debugging
        self.event_history: List[GameEvent] = []
        self.max_history_size = 1000
        
        # Subscribers by event type
        self.subscribers: Dict[EventType, WeakSet[IEventHandler]] = {}
        
        # Lock for thread safety
        self.publish_lock = asyncio.Lock()
        
    async def start(self):
        """Start the event bus processing."""
        if self.is_running:
            logger.warning(f"Event bus already running for room {self.room_id}")
            return
        
        logger.info(f"🚀 Starting event bus for room {self.room_id}")
        self.is_running = True
        
        # Start processing tasks for each priority level
        for priority in EventPriority:
            task = asyncio.create_task(
                self._process_priority_queue(priority),
                name=f"EventBus-{priority.name}-{self.room_id}"
            )
            self.processing_tasks.add(task)
        
        logger.info(f"✅ Event bus started with {len(self.processing_tasks)} processing tasks")
    
    async def stop(self):
        """Stop the event bus and cleanup resources."""
        if not self.is_running:
            return
        
        logger.info(f"🛑 Stopping event bus for room {self.room_id}")
        self.is_running = False
        
        # Cancel all processing tasks
        for task in self.processing_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.processing_tasks, return_exceptions=True)
        self.processing_tasks.clear()
        
        # Clear all queues
        for queue in self.event_queues.values():
            while not queue.empty():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
        
        logger.info(f"✅ Event bus stopped. Final metrics: {self.metrics}")
    
    async def publish(self, event: GameEvent, **kwargs):
        """
        Publish an event to the event bus.
        
        Args:
            event: The event to publish
            **kwargs: Additional event data
        """
        async with self.publish_lock:
            try:
                # Update event data if provided
                if kwargs:
                    event.data.update(kwargs)
                
                # Set room ID if not set
                if not event.room_id and self.room_id:
                    event.room_id = self.room_id
                
                # Apply middleware preprocessing
                for middleware in self.middleware:
                    event = await middleware.pre_process(event)
                    if event.is_cancelled:
                        logger.debug(f"Event {event.event_id} cancelled by middleware")
                        return
                
                # Apply event filters
                if not await self._apply_filters(event):
                    logger.debug(f"Event {event.event_id} filtered out")
                    return
                
                # Add to priority queue
                priority_queue = self.event_queues[event.priority]
                await priority_queue.put(event)
                
                # Update metrics
                self.metrics.events_published += 1
                
                # Add to history
                self._add_to_history(event)
                
                logger.debug(f"📡 PUBLISHED: {event.event_type.value} (priority: {event.priority.name})")
                
            except Exception as e:
                logger.error(f"❌ PUBLISH_ERROR: Failed to publish event {event.event_id}: {str(e)}")
                self.metrics.events_failed += 1
                raise
    
    async def _process_priority_queue(self, priority: EventPriority):
        """Process events from a specific priority queue."""
        queue = self.event_queues[priority]
        
        while self.is_running:
            try:
                # Wait for next event with timeout
                event = await asyncio.wait_for(queue.get(), timeout=1.0)
                
                # Process the event
                await self._process_event(event)
                
                # Mark task as done
                queue.task_done()
                
            except asyncio.TimeoutError:
                # Normal timeout, continue processing
                continue
            except Exception as e:
                logger.error(f"❌ QUEUE_PROCESS_ERROR: Error processing {priority.name} queue: {str(e)}")
                self.metrics.events_failed += 1
    
    async def _process_event(self, event: GameEvent):
        """Process a single event through the handler pipeline."""
        start_time = datetime.now()
        
        try:
            logger.debug(f"⚡ PROCESSING: {event.event_type.value} (ID: {event.event_id})")
            
            # Get handlers for this event type
            handlers = self.handler_registry.get_handlers(event.event_type)
            
            if not handlers:
                logger.debug(f"No handlers registered for {event.event_type.value}")
                return
            
            # Process through each handler
            for handler in handlers:
                try:
                    # Apply middleware pre-handler processing
                    for middleware in self.middleware:
                        event = await middleware.pre_handle(event, handler)
                        if event.is_cancelled:
                            logger.debug(f"Event {event.event_id} cancelled by middleware before handler")
                            return
                    
                    # Execute handler
                    await handler.handle(event)
                    
                    # Apply middleware post-handler processing
                    for middleware in self.middleware:
                        await middleware.post_handle(event, handler)
                    
                except Exception as e:
                    logger.error(f"❌ HANDLER_ERROR: Handler {handler.__class__.__name__} failed: {str(e)}")
                    event.add_error(f"Handler {handler.__class__.__name__}: {str(e)}")
                    self.metrics.events_failed += 1
            
            # Mark event as processed
            event.mark_processed()
            
            # Apply middleware post-processing
            for middleware in self.middleware:
                await middleware.post_process(event)
            
            # Update metrics
            self.metrics.events_processed += 1
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_processing_time(processing_time)
            
            logger.debug(f"✅ PROCESSED: {event.event_type.value} in {processing_time:.3f}s")
            
        except Exception as e:
            logger.error(f"❌ PROCESS_ERROR: Failed to process event {event.event_id}: {str(e)}")
            event.add_error(f"Processing error: {str(e)}")
            self.metrics.events_failed += 1
    
    def subscribe(self, event_type: EventType, handler: IEventHandler):
        """Subscribe a handler to an event type."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = WeakSet()
        
        self.subscribers[event_type].add(handler)
        self.handler_registry.register_handler(event_type, handler)
        self.metrics.handlers_registered += 1
        
        logger.debug(f"📝 SUBSCRIBED: {handler.__class__.__name__} to {event_type.value}")
    
    def unsubscribe(self, event_type: EventType, handler: IEventHandler):
        """Unsubscribe a handler from an event type."""
        if event_type in self.subscribers:
            self.subscribers[event_type].discard(handler)
        
        self.handler_registry.unregister_handler(event_type, handler)
        self.metrics.handlers_registered -= 1
        
        logger.debug(f"📝 UNSUBSCRIBED: {handler.__class__.__name__} from {event_type.value}")
    
    def add_middleware(self, middleware: IEventMiddleware):
        """Add middleware to the processing pipeline."""
        self.middleware.append(middleware)
        self.metrics.middleware_count += 1
        
        logger.debug(f"⚙️ MIDDLEWARE_ADDED: {middleware.__class__.__name__}")
    
    def remove_middleware(self, middleware: IEventMiddleware):
        """Remove middleware from the processing pipeline."""
        if middleware in self.middleware:
            self.middleware.remove(middleware)
            self.metrics.middleware_count -= 1
            
            logger.debug(f"⚙️ MIDDLEWARE_REMOVED: {middleware.__class__.__name__}")
    
    def add_filter(self, event_type: EventType, filter_func: Callable[[GameEvent], bool]):
        """Add an event filter for a specific event type."""
        if event_type not in self.event_filters:
            self.event_filters[event_type] = []
        
        self.event_filters[event_type].append(filter_func)
        logger.debug(f"🔍 FILTER_ADDED: Filter for {event_type.value}")
    
    async def _apply_filters(self, event: GameEvent) -> bool:
        """Apply event filters to determine if event should be processed."""
        filters = self.event_filters.get(event.event_type, [])
        
        for filter_func in filters:
            try:
                if not filter_func(event):
                    logger.debug(f"🔍 FILTERED: Event {event.event_id} filtered out")
                    return False
            except Exception as e:
                logger.error(f"❌ FILTER_ERROR: Filter function failed: {str(e)}")
                # Continue processing if filter fails
        
        return True
    
    def _add_to_history(self, event: GameEvent):
        """Add event to history for debugging."""
        self.event_history.append(event)
        
        # Trim history if too large
        if len(self.event_history) > self.max_history_size:
            self.event_history = self.event_history[-self.max_history_size:]
    
    def _update_processing_time(self, processing_time: float):
        """Update average processing time metric."""
        if self.metrics.events_processed == 1:
            self.metrics.average_processing_time = processing_time
        else:
            # Running average
            self.metrics.average_processing_time = (
                (self.metrics.average_processing_time * (self.metrics.events_processed - 1) + processing_time) 
                / self.metrics.events_processed
            )
    
    def get_metrics(self) -> EventBusMetrics:
        """Get current event bus metrics."""
        return self.metrics
    
    def get_event_history(self, limit: int = 100) -> List[GameEvent]:
        """Get recent event history."""
        return self.event_history[-limit:]
    
    def get_queue_sizes(self) -> Dict[str, int]:
        """Get current queue sizes for monitoring."""
        return {
            priority.name: queue.qsize()
            for priority, queue in self.event_queues.items()
        }


# Global event bus instances
_global_event_buses: Dict[str, EventBus] = {}
_default_event_bus: Optional[EventBus] = None


def get_global_event_bus(room_id: Optional[str] = None) -> EventBus:
    """
    Get or create a global event bus instance.
    
    Args:
        room_id: Optional room ID for room-scoped event bus
        
    Returns:
        EventBus instance
    """
    global _global_event_buses, _default_event_bus
    
    if room_id:
        if room_id not in _global_event_buses:
            _global_event_buses[room_id] = EventBus(room_id)
        return _global_event_buses[room_id]
    else:
        if _default_event_bus is None:
            _default_event_bus = EventBus()
        return _default_event_bus


async def reset_global_event_bus(room_id: Optional[str] = None):
    """Reset global event bus instances."""
    global _global_event_buses, _default_event_bus
    
    if room_id:
        if room_id in _global_event_buses:
            await _global_event_buses[room_id].stop()
            del _global_event_buses[room_id]
    else:
        if _default_event_bus:
            await _default_event_bus.stop()
            _default_event_bus = None