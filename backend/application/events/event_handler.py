# application/events/event_handler.py
"""
Base classes for event handlers.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional
import logging

from domain.events.base import DomainEvent

logger = logging.getLogger(__name__)

TEvent = TypeVar('TEvent', bound=DomainEvent)


class EventHandler(ABC, Generic[TEvent]):
    """
    Base class for synchronous event handlers.
    
    Event handlers react to domain events and perform side effects
    like updating read models, sending notifications, or triggering
    other processes.
    """
    
    @abstractmethod
    def handle(self, event: TEvent) -> None:
        """
        Handle the event.
        
        This method should be idempotent - handling the same event
        multiple times should have the same effect as handling it once.
        """
        pass
    
    def can_handle(self, event: DomainEvent) -> bool:
        """
        Check if this handler can handle the given event.
        
        Override this method to add custom filtering logic.
        """
        return True


class AsyncEventHandler(ABC, Generic[TEvent]):
    """
    Base class for asynchronous event handlers.
    
    Use this for handlers that need to perform async operations
    like making HTTP calls or database queries.
    """
    
    @abstractmethod
    async def handle(self, event: TEvent) -> None:
        """
        Handle the event asynchronously.
        
        This method should be idempotent.
        """
        pass
    
    async def can_handle(self, event: DomainEvent) -> bool:
        """
        Check if this handler can handle the given event.
        
        Override this method to add custom filtering logic.
        """
        return True


class CompositeEventHandler(EventHandler[DomainEvent]):
    """
    Composite handler that delegates to multiple handlers.
    
    Useful for grouping related handlers together.
    """
    
    def __init__(self, handlers: List[EventHandler] = None):
        """Initialize with optional list of handlers."""
        self._handlers = handlers or []
    
    def add_handler(self, handler: EventHandler) -> None:
        """Add a handler to the composite."""
        self._handlers.append(handler)
    
    def remove_handler(self, handler: EventHandler) -> None:
        """Remove a handler from the composite."""
        self._handlers.remove(handler)
    
    def handle(self, event: DomainEvent) -> None:
        """Handle event by delegating to all child handlers."""
        for handler in self._handlers:
            if handler.can_handle(event):
                try:
                    handler.handle(event)
                except Exception as e:
                    logger.error(
                        f"Error in handler {handler.__class__.__name__}: {str(e)}",
                        exc_info=True
                    )


class BatchEventHandler(AsyncEventHandler[DomainEvent]):
    """
    Handler that batches events for efficient processing.
    
    Useful for handlers that can process multiple events more
    efficiently than processing them one by one.
    """
    
    def __init__(self, batch_size: int = 10, flush_interval: float = 1.0):
        """
        Initialize batch handler.
        
        Args:
            batch_size: Maximum number of events to batch
            flush_interval: Maximum time to wait before flushing (seconds)
        """
        self._batch_size = batch_size
        self._flush_interval = flush_interval
        self._batch: List[DomainEvent] = []
        self._last_flush = None
    
    async def handle(self, event: DomainEvent) -> None:
        """Add event to batch and flush if needed."""
        self._batch.append(event)
        
        if len(self._batch) >= self._batch_size:
            await self._flush()
    
    async def _flush(self) -> None:
        """Flush the current batch."""
        if not self._batch:
            return
        
        try:
            await self._process_batch(self._batch[:])
            self._batch.clear()
        except Exception as e:
            logger.error(f"Error processing batch: {str(e)}", exc_info=True)
            raise
    
    @abstractmethod
    async def _process_batch(self, events: List[DomainEvent]) -> None:
        """Process a batch of events. Override in subclasses."""
        pass