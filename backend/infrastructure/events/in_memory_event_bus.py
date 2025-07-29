"""
In-memory event bus implementation.

Provides a simple event bus for publishing and subscribing to domain events.
This is suitable for single-process applications.
"""

from typing import Dict, List, Callable, Any, Type
from domain.events.base import DomainEvent
from domain.interfaces.events import EventPublisher, EventHandler
import asyncio
import logging
import inspect

logger = logging.getLogger(__name__)


class InMemoryEventBus(EventPublisher):
    """
    Simple in-memory event bus implementation.
    
    Allows handlers to subscribe to specific event types and
    dispatches events to appropriate handlers.
    """
    
    def __init__(self):
        """Initialize with empty handler registry."""
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._global_handlers: List[EventHandler] = []
    
    def register_handler(self, handler: EventHandler) -> None:
        """
        Register an event handler.
        
        Args:
            handler: Handler to register
        """
        # Register for specific event types
        for event_type in handler.get_event_types():
            # Use the event type's name as key for consistency
            event_type_name = event_type.__name__ if hasattr(event_type, '__name__') else str(event_type)
            if event_type_name not in self._handlers:
                self._handlers[event_type_name] = []
            self._handlers[event_type_name].append(handler)
            logger.debug(f"Registered handler {handler.__class__.__name__} for {event_type_name}")
    
    def register_global_handler(self, handler: EventHandler) -> None:
        """
        Register a handler that receives all events.
        
        Args:
            handler: Handler to register globally
        """
        self._global_handlers.append(handler)
        logger.debug(f"Registered global handler {handler.__class__.__name__}")
    
    def subscribe(self, event_type: Type[DomainEvent], handler_func: Callable, priority: int = 0) -> None:
        """
        Subscribe a function to handle a specific event type.
        
        This is a convenience method that wraps a function as an EventHandler.
        
        Args:
            event_type: The event type to subscribe to
            handler_func: Async function that takes the event as parameter
            priority: Handler priority (higher = called first) - currently ignored
        """
        # Store handler directly by event type name
        event_type_name = event_type.__name__ if hasattr(event_type, '__name__') else str(event_type)
        
        # Create a wrapper that can be called directly
        async def wrapper(event: DomainEvent):
            if isinstance(event, event_type):
                if inspect.iscoroutinefunction(handler_func):
                    await handler_func(event)
                else:
                    handler_func(event)
        
        # Store as a simple callable
        if event_type_name not in self._handlers:
            self._handlers[event_type_name] = []
        self._handlers[event_type_name].append(wrapper)
        logger.info(f"Subscribed function {handler_func.__name__} to {event_type_name}")
    
    async def publish(self, event: DomainEvent) -> None:
        """
        Publish a single domain event.
        
        Args:
            event: Domain event to publish
        """
        event_type = event.__class__.__name__
        logger.info(f"[EVENT_BUS_DEBUG] Publishing event {event_type}")
        
        # Notify specific handlers
        handlers = self._handlers.get(event_type, [])
        
        # Combine with global handlers
        all_handlers = handlers + self._global_handlers
        
        if not all_handlers:
            logger.warning(f"[EVENT_BUS_DEBUG] No handlers for event {event_type}")
            logger.warning(f"[EVENT_BUS_DEBUG] Registered handlers: {list(self._handlers.keys())}")
            return
        
        logger.info(f"[EVENT_BUS_DEBUG] Found {len(all_handlers)} handlers for {event_type}")
        
        # Execute handlers concurrently
        tasks = []
        for handler in all_handlers:
            # Check if it's an EventHandler object or a callable
            if hasattr(handler, 'can_handle'):
                # It's an EventHandler object
                if handler.can_handle(event):
                    tasks.append(self._handle_event(handler, event))
            else:
                # It's a callable function
                tasks.append(self._handle_callable(handler, event))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def publish_batch(self, events: List[DomainEvent]) -> None:
        """
        Publish multiple events as a batch.
        
        Args:
            events: List of domain events to publish
        """
        # For simplicity, publish each event individually
        # A more sophisticated implementation might optimize batch handling
        for event in events:
            await self.publish(event)
    
    async def _handle_event(self, handler: EventHandler, event: DomainEvent) -> None:
        """
        Handle an event with error handling.
        
        Args:
            handler: Handler to execute
            event: Event to handle
        """
        try:
            await handler.handle(event)
        except Exception as e:
            logger.error(
                f"Error in handler {handler.__class__.__name__} "
                f"for event {event.__class__.__name__}: {e}"
            )
    
    async def _handle_callable(self, handler_func: Callable, event: DomainEvent) -> None:
        """
        Handle an event with a callable function.
        
        Args:
            handler_func: Callable to execute
            event: Event to handle
        """
        try:
            await handler_func(event)
        except Exception as e:
            logger.error(
                f"Error in handler function "
                f"for event {event.__class__.__name__}: {e}",
                exc_info=True
            )
    
    def clear_handlers(self) -> None:
        """Clear all registered handlers."""
        self._handlers.clear()
        self._global_handlers.clear()


# Singleton instance
_event_bus = None


def get_event_bus() -> InMemoryEventBus:
    """
    Get the singleton event bus instance.
    
    Returns:
        The event bus instance
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = InMemoryEventBus()
    return _event_bus