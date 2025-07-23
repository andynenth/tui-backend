# application/events/event_bus.py
"""
Event bus implementation for decoupled event handling.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Dict, List, Set, Type, Callable, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
import traceback

from domain.events.base import DomainEvent

logger = logging.getLogger(__name__)


@dataclass
class EventSubscription:
    """Represents a subscription to an event type."""
    event_type: Type[DomainEvent]
    handler: Callable
    priority: int = 0
    filter_predicate: Callable[[DomainEvent], bool] = None
    
    def __post_init__(self):
        """Validate subscription."""
        if not callable(self.handler):
            raise ValueError("Handler must be callable")


class EventBus(ABC):
    """
    Abstract base class for event bus implementations.
    
    The event bus provides a decoupled way for different parts
    of the application to communicate through events.
    """
    
    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """Publish an event to all registered handlers."""
        pass
    
    @abstractmethod
    def subscribe(
        self,
        event_type: Type[DomainEvent],
        handler: Callable[[DomainEvent], Any],
        priority: int = 0,
        filter_predicate: Callable[[DomainEvent], bool] = None
    ) -> None:
        """Subscribe a handler to an event type."""
        pass
    
    @abstractmethod
    def unsubscribe(
        self,
        event_type: Type[DomainEvent],
        handler: Callable[[DomainEvent], Any]
    ) -> None:
        """Unsubscribe a handler from an event type."""
        pass
    
    @abstractmethod
    def clear_subscriptions(self) -> None:
        """Clear all subscriptions."""
        pass


class InMemoryEventBus(EventBus):
    """
    In-memory implementation of the event bus.
    
    Features:
    - Priority-based handler execution
    - Async and sync handler support
    - Error isolation (one handler failing doesn't affect others)
    - Optional filtering of events
    - Metrics tracking
    """
    
    def __init__(self, error_handler: Callable[[Exception, DomainEvent], None] = None):
        """
        Initialize the event bus.
        
        Args:
            error_handler: Optional custom error handler for failed event processing
        """
        self._subscriptions: Dict[Type[DomainEvent], List[EventSubscription]] = defaultdict(list)
        self._error_handler = error_handler or self._default_error_handler
        self._metrics = EventBusMetrics()
        self._processing_events: Set[str] = set()  # Track events being processed
        
    async def publish(self, event: DomainEvent) -> None:
        """
        Publish an event to all registered handlers.
        
        Handlers are executed in priority order (higher priority first).
        Errors in one handler don't affect others.
        """
        if not isinstance(event, DomainEvent):
            raise ValueError(f"Event must be a DomainEvent, got {type(event)}")
        
        # Check for circular events
        event_key = f"{type(event).__name__}:{event.aggregate_id}"
        if event_key in self._processing_events:
            logger.warning(f"Circular event detected, skipping: {event_key}")
            return
        
        self._processing_events.add(event_key)
        try:
            await self._process_event(event)
        finally:
            self._processing_events.discard(event_key)
    
    async def _process_event(self, event: DomainEvent) -> None:
        """Process an event through all subscribed handlers."""
        event_type = type(event)
        self._metrics.events_published += 1
        
        # Get all subscriptions for this event type and its base classes
        all_subscriptions = []
        for cls in event_type.__mro__:
            if issubclass(cls, DomainEvent) and cls in self._subscriptions:
                all_subscriptions.extend(self._subscriptions[cls])
        
        if not all_subscriptions:
            logger.debug(f"No handlers for event {event_type.__name__}")
            return
        
        # Sort by priority (descending)
        sorted_subscriptions = sorted(
            all_subscriptions,
            key=lambda s: s.priority,
            reverse=True
        )
        
        # Execute handlers
        tasks = []
        for subscription in sorted_subscriptions:
            # Apply filter if present
            if subscription.filter_predicate and not subscription.filter_predicate(event):
                continue
            
            task = self._execute_handler(subscription, event)
            tasks.append(task)
        
        # Wait for all handlers to complete
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log any exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    handler = sorted_subscriptions[i].handler
                    self._error_handler(result, event)
                    self._metrics.handler_errors += 1
    
    async def _execute_handler(
        self,
        subscription: EventSubscription,
        event: DomainEvent
    ) -> None:
        """Execute a single handler."""
        handler = subscription.handler
        handler_name = getattr(handler, '__name__', str(handler))
        
        try:
            logger.debug(f"Executing handler {handler_name} for {type(event).__name__}")
            
            # Check if handler is async
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                # Run sync handler in thread pool
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, handler, event)
            
            self._metrics.handlers_executed += 1
            
        except Exception as e:
            logger.error(
                f"Error in event handler {handler_name}: {str(e)}",
                exc_info=True
            )
            raise
    
    def subscribe(
        self,
        event_type: Type[DomainEvent],
        handler: Callable[[DomainEvent], Any],
        priority: int = 0,
        filter_predicate: Callable[[DomainEvent], bool] = None
    ) -> None:
        """
        Subscribe a handler to an event type.
        
        Args:
            event_type: The event type to subscribe to
            handler: The handler function (can be async or sync)
            priority: Handler priority (higher executes first)
            filter_predicate: Optional filter to conditionally handle events
        """
        if not issubclass(event_type, DomainEvent):
            raise ValueError(f"Event type must be a DomainEvent subclass, got {event_type}")
        
        subscription = EventSubscription(
            event_type=event_type,
            handler=handler,
            priority=priority,
            filter_predicate=filter_predicate
        )
        
        self._subscriptions[event_type].append(subscription)
        logger.info(f"Subscribed {handler} to {event_type.__name__}")
    
    def unsubscribe(
        self,
        event_type: Type[DomainEvent],
        handler: Callable[[DomainEvent], Any]
    ) -> None:
        """Unsubscribe a handler from an event type."""
        if event_type in self._subscriptions:
            self._subscriptions[event_type] = [
                s for s in self._subscriptions[event_type]
                if s.handler != handler
            ]
            logger.info(f"Unsubscribed {handler} from {event_type.__name__}")
    
    def clear_subscriptions(self) -> None:
        """Clear all subscriptions."""
        self._subscriptions.clear()
        logger.info("Cleared all event subscriptions")
    
    def _default_error_handler(self, error: Exception, event: DomainEvent) -> None:
        """Default error handler logs the error."""
        logger.error(
            f"Error handling event {type(event).__name__}: {str(error)}",
            extra={
                'event_id': event.event_id,
                'aggregate_id': event.aggregate_id,
                'error_type': type(error).__name__,
                'traceback': traceback.format_exc()
            }
        )
    
    def get_metrics(self) -> 'EventBusMetrics':
        """Get event bus metrics."""
        return self._metrics


@dataclass
class EventBusMetrics:
    """Metrics for event bus performance monitoring."""
    events_published: int = 0
    handlers_executed: int = 0
    handler_errors: int = 0
    
    def reset(self):
        """Reset all metrics."""
        self.events_published = 0
        self.handlers_executed = 0
        self.handler_errors = 0