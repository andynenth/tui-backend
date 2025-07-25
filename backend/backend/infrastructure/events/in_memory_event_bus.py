"""
In-memory implementation of the event bus.

This implementation is suitable for single-process applications
and provides high performance event distribution.
"""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Type, Set, Optional
from datetime import datetime

from domain.interfaces.event_publisher import EventBus, EventHandler
from domain.events.base import DomainEvent


logger = logging.getLogger(__name__)


@dataclass
class HandlerInfo:
    """Information about a registered event handler."""
    handler: EventHandler
    priority: int
    
    def __lt__(self, other):
        # Higher priority handlers are called first
        return self.priority > other.priority


class InMemoryEventBus(EventBus):
    """
    In-memory event bus implementation.
    
    Features:
    - Async event handling
    - Priority-based handler ordering
    - Error isolation (one handler failure doesn't affect others)
    - Event history tracking
    - Performance metrics
    """
    
    def __init__(self, track_history: bool = True, max_history_size: int = 1000):
        """
        Initialize the event bus.
        
        Args:
            track_history: Whether to keep event history
            max_history_size: Maximum events to keep in history
        """
        self._handlers: Dict[Type[DomainEvent], List[HandlerInfo]] = defaultdict(list)
        self._track_history = track_history
        self._max_history_size = max_history_size
        self._event_history: List[DomainEvent] = []
        self._metrics = {
            'events_published': 0,
            'events_handled': 0,
            'handler_errors': 0,
            'total_handlers_called': 0
        }
        self._sequence_number = 0
    
    async def publish(self, event: DomainEvent) -> None:
        """Publish a single event to all registered handlers."""
        await self._publish_event(event)
    
    async def publish_batch(self, events: List[DomainEvent]) -> None:
        """Publish multiple events."""
        # Process events sequentially to maintain order
        for event in events:
            await self._publish_event(event)
    
    async def _publish_event(self, event: DomainEvent) -> None:
        """Internal method to publish a single event."""
        # Add sequence number to event metadata
        self._sequence_number += 1
        event.metadata.sequence_number = self._sequence_number
        
        # Track metrics
        self._metrics['events_published'] += 1
        
        # Store in history if enabled
        if self._track_history:
            self._event_history.append(event)
            # Trim history if too large
            if len(self._event_history) > self._max_history_size:
                self._event_history = self._event_history[-self._max_history_size:]
        
        # Get handlers for this event type and its parent types
        handlers = self._get_all_handlers_for_event(event)
        
        if not handlers:
            logger.debug(f"No handlers registered for event type: {event.event_type}")
            return
        
        # Execute handlers
        tasks = []
        for handler_info in handlers:
            task = self._execute_handler(handler_info.handler, event)
            tasks.append(task)
        
        # Wait for all handlers to complete
        await asyncio.gather(*tasks, return_exceptions=True)
        
        self._metrics['events_handled'] += 1
    
    def _get_all_handlers_for_event(self, event: DomainEvent) -> List[HandlerInfo]:
        """Get all handlers that should handle this event."""
        handlers = []
        
        # Get handlers for the exact event type
        event_type = type(event)
        if event_type in self._handlers:
            handlers.extend(self._handlers[event_type])
        
        # Get handlers for parent types (e.g., GameEvent handlers for specific game events)
        for base_type in event_type.__mro__[1:]:
            if base_type in self._handlers and issubclass(base_type, DomainEvent):
                handlers.extend(self._handlers[base_type])
        
        # Sort by priority
        handlers.sort()
        
        return handlers
    
    async def _execute_handler(self, handler: EventHandler, event: DomainEvent) -> None:
        """Execute a single handler with error isolation."""
        try:
            self._metrics['total_handlers_called'] += 1
            await handler(event)
        except Exception as e:
            self._metrics['handler_errors'] += 1
            logger.error(
                f"Error in event handler for {event.event_type}: {e}",
                exc_info=True,
                extra={
                    'event_id': event.metadata.event_id,
                    'event_type': event.event_type,
                    'handler': handler.__name__ if hasattr(handler, '__name__') else str(handler)
                }
            )
    
    def subscribe(
        self,
        event_type: Type[DomainEvent],
        handler: EventHandler,
        priority: int = 0
    ) -> None:
        """Subscribe a handler to an event type."""
        handler_info = HandlerInfo(handler=handler, priority=priority)
        
        # Check if handler already registered
        for existing in self._handlers[event_type]:
            if existing.handler == handler:
                # Update priority if different
                if existing.priority != priority:
                    existing.priority = priority
                    self._handlers[event_type].sort()
                return
        
        # Add new handler
        self._handlers[event_type].append(handler_info)
        self._handlers[event_type].sort()
        
        logger.debug(
            f"Handler {handler.__name__ if hasattr(handler, '__name__') else 'anonymous'} "
            f"subscribed to {event_type.__name__} with priority {priority}"
        )
    
    def unsubscribe(
        self,
        event_type: Type[DomainEvent],
        handler: EventHandler
    ) -> None:
        """Unsubscribe a handler from an event type."""
        if event_type not in self._handlers:
            return
        
        self._handlers[event_type] = [
            h for h in self._handlers[event_type]
            if h.handler != handler
        ]
        
        # Remove empty handler lists
        if not self._handlers[event_type]:
            del self._handlers[event_type]
    
    def get_handlers(self, event_type: Type[DomainEvent]) -> List[EventHandler]:
        """Get all handlers for an event type."""
        if event_type not in self._handlers:
            return []
        
        return [h.handler for h in self._handlers[event_type]]
    
    def get_event_history(self, limit: Optional[int] = None) -> List[DomainEvent]:
        """Get event history."""
        if not self._track_history:
            return []
        
        if limit:
            return self._event_history[-limit:]
        return list(self._event_history)
    
    def get_metrics(self) -> Dict[str, int]:
        """Get event bus metrics."""
        return dict(self._metrics)
    
    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()
    
    def reset_metrics(self) -> None:
        """Reset metrics counters."""
        for key in self._metrics:
            self._metrics[key] = 0


# Global event bus instance
_event_bus: Optional[InMemoryEventBus] = None


def get_event_bus() -> InMemoryEventBus:
    """Get the global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = InMemoryEventBus()
    return _event_bus


def reset_event_bus() -> None:
    """Reset the global event bus (useful for testing)."""
    global _event_bus
    _event_bus = None