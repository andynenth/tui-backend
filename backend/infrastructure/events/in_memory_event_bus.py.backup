"""
In-memory event bus implementation.

Provides a simple event bus for publishing and subscribing to domain events.
This is suitable for single-process applications.
"""

from typing import Dict, List, Callable, Any
from domain.events.base import DomainEvent
from domain.interfaces.events import EventPublisher, EventHandler
import asyncio
import logging

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
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(handler)
            logger.debug(f"Registered handler {handler.__class__.__name__} for {event_type}")
    
    def register_global_handler(self, handler: EventHandler) -> None:
        """
        Register a handler that receives all events.
        
        Args:
            handler: Handler to register globally
        """
        self._global_handlers.append(handler)
        logger.debug(f"Registered global handler {handler.__class__.__name__}")
    
    async def publish(self, event: DomainEvent) -> None:
        """
        Publish a single domain event.
        
        Args:
            event: Domain event to publish
        """
        event_type = event.__class__.__name__
        
        # Notify specific handlers
        handlers = self._handlers.get(event_type, [])
        
        # Combine with global handlers
        all_handlers = handlers + self._global_handlers
        
        if not all_handlers:
            logger.debug(f"No handlers for event {event_type}")
            return
        
        # Execute handlers concurrently
        tasks = []
        for handler in all_handlers:
            if handler.can_handle(event):
                tasks.append(self._handle_event(handler, event))
        
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