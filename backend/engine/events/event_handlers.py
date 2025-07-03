# backend/engine/events/event_handlers.py

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Set, Optional, Callable, Any
from weakref import WeakSet
from datetime import datetime

from .event_types import GameEvent, EventType

logger = logging.getLogger(__name__)


class IEventHandler(ABC):
    """
    🎯 **Event Handler Interface** - Abstract base for all event handlers
    
    Defines the contract for event processing with async support and error handling.
    """
    
    @abstractmethod
    async def handle(self, event: GameEvent) -> Any:
        """
        Handle a game event.
        
        Args:
            event: The event to handle
            
        Returns:
            Optional result from event processing
        """
        pass
    
    @abstractmethod
    def can_handle(self, event_type: EventType) -> bool:
        """
        Check if this handler can process the given event type.
        
        Args:
            event_type: The event type to check
            
        Returns:
            True if handler can process this event type
        """
        pass
    
    def get_handler_name(self) -> str:
        """Get human-readable handler name."""
        return self.__class__.__name__
    
    def get_supported_events(self) -> Set[EventType]:
        """Get all event types this handler supports."""
        return {event_type for event_type in EventType if self.can_handle(event_type)}


class EventHandler(IEventHandler):
    """
    🎯 **Base Event Handler** - Concrete base class for event handlers
    
    Provides common functionality for event processing with configurable
    event type filtering and error handling.
    """
    
    def __init__(self, supported_events: Set[EventType]):
        self.supported_events = supported_events
        self.processed_count = 0
        self.error_count = 0
        self.last_processed = None
        
    async def handle(self, event: GameEvent) -> Any:
        """Handle an event with error tracking."""
        try:
            if not self.can_handle(event.event_type):
                logger.warning(f"⚠️ Handler {self.get_handler_name()} cannot handle {event.event_type.value}")
                return None
            
            # Delegate to specific handler implementation
            result = await self._handle_event(event)
            
            # Update metrics
            self.processed_count += 1
            self.last_processed = datetime.now()
            
            return result
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"❌ Handler {self.get_handler_name()} failed: {str(e)}")
            raise
    
    def can_handle(self, event_type: EventType) -> bool:
        """Check if this handler supports the event type."""
        return event_type in self.supported_events
    
    @abstractmethod
    async def _handle_event(self, event: GameEvent) -> Any:
        """
        Override this method to implement event handling logic.
        
        Args:
            event: The event to handle
            
        Returns:
            Optional result from event processing
        """
        pass
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get handler performance metrics."""
        return {
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "last_processed": self.last_processed.isoformat() if self.last_processed else None,
            "supported_events": [event.value for event in self.supported_events]
        }


class AsyncEventHandler(EventHandler):
    """
    🎯 **Async Event Handler** - Handler with async execution control
    
    Supports concurrent event processing with configurable concurrency limits
    and task management.
    """
    
    def __init__(self, supported_events: Set[EventType], max_concurrent: int = 10):
        super().__init__(supported_events)
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_tasks: Set[asyncio.Task] = set()
        
    async def handle(self, event: GameEvent) -> Any:
        """Handle event with concurrency control."""
        async with self.semaphore:
            return await super().handle(event)
    
    async def handle_concurrent(self, event: GameEvent) -> asyncio.Task:
        """
        Handle event concurrently without waiting for completion.
        
        Args:
            event: The event to handle
            
        Returns:
            Task representing the async operation
        """
        task = asyncio.create_task(self.handle(event))
        self.active_tasks.add(task)
        
        # Clean up completed tasks
        task.add_done_callback(self.active_tasks.discard)
        
        return task
    
    async def wait_for_all_tasks(self, timeout: Optional[float] = None):
        """Wait for all active tasks to complete."""
        if not self.active_tasks:
            return
        
        try:
            await asyncio.wait_for(
                asyncio.gather(*self.active_tasks, return_exceptions=True),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"⏳ Handler {self.get_handler_name()} tasks timed out")
    
    async def cancel_all_tasks(self):
        """Cancel all active tasks."""
        for task in self.active_tasks:
            task.cancel()
        
        if self.active_tasks:
            await asyncio.gather(*self.active_tasks, return_exceptions=True)
            self.active_tasks.clear()


class EventHandlerRegistry:
    """
    🎯 **Event Handler Registry** - Central registry for event handlers
    
    Manages handler registration, lookup, and cleanup with weak references
    to prevent memory leaks.
    """
    
    def __init__(self):
        # Use WeakSet to automatically cleanup dead references
        self.handlers: Dict[EventType, WeakSet[IEventHandler]] = {}
        self.named_handlers: Dict[str, IEventHandler] = {}
        self.handler_stats: Dict[str, Dict[str, Any]] = {}
        
    def register_handler(self, event_type: EventType, handler: IEventHandler, name: Optional[str] = None):
        """
        Register an event handler for a specific event type.
        
        Args:
            event_type: The event type to register for
            handler: The handler instance
            name: Optional name for the handler
        """
        if event_type not in self.handlers:
            self.handlers[event_type] = WeakSet()
        
        self.handlers[event_type].add(handler)
        
        # Register named handler if name provided
        if name:
            self.named_handlers[name] = handler
        
        # Initialize stats
        handler_name = name or handler.get_handler_name()
        self.handler_stats[handler_name] = {
            "registered_at": datetime.now().isoformat(),
            "event_types": [event_type.value],
            "handler_class": handler.__class__.__name__
        }
        
        logger.debug(f"📝 REGISTERED: {handler_name} for {event_type.value}")
    
    def register_multi_handler(self, event_types: Set[EventType], handler: IEventHandler, name: Optional[str] = None):
        """
        Register a handler for multiple event types.
        
        Args:
            event_types: Set of event types to register for
            handler: The handler instance
            name: Optional name for the handler
        """
        for event_type in event_types:
            self.register_handler(event_type, handler, name)
        
        # Update stats for multi-registration
        handler_name = name or handler.get_handler_name()
        if handler_name in self.handler_stats:
            self.handler_stats[handler_name]["event_types"] = [et.value for et in event_types]
    
    def unregister_handler(self, event_type: EventType, handler: IEventHandler):
        """
        Unregister an event handler.
        
        Args:
            event_type: The event type to unregister from
            handler: The handler instance
        """
        if event_type in self.handlers:
            self.handlers[event_type].discard(handler)
            
            # Clean up empty sets
            if not self.handlers[event_type]:
                del self.handlers[event_type]
        
        # Remove from named handlers
        handler_name = handler.get_handler_name()
        if handler_name in self.named_handlers:
            del self.named_handlers[handler_name]
        
        # Remove stats
        if handler_name in self.handler_stats:
            del self.handler_stats[handler_name]
        
        logger.debug(f"📝 UNREGISTERED: {handler_name} from {event_type.value}")
    
    def get_handlers(self, event_type: EventType) -> List[IEventHandler]:
        """
        Get all handlers for a specific event type.
        
        Args:
            event_type: The event type to get handlers for
            
        Returns:
            List of handlers for the event type
        """
        if event_type not in self.handlers:
            return []
        
        # Convert WeakSet to list and filter out None values
        handlers = [handler for handler in self.handlers[event_type] if handler is not None]
        return handlers
    
    def get_handler_by_name(self, name: str) -> Optional[IEventHandler]:
        """
        Get a handler by its registered name.
        
        Args:
            name: The handler name
            
        Returns:
            Handler instance if found, None otherwise
        """
        return self.named_handlers.get(name)
    
    def get_all_handlers(self) -> Dict[EventType, List[IEventHandler]]:
        """Get all registered handlers grouped by event type."""
        return {
            event_type: self.get_handlers(event_type)
            for event_type in self.handlers.keys()
        }
    
    def get_handler_count(self, event_type: Optional[EventType] = None) -> int:
        """
        Get the number of registered handlers.
        
        Args:
            event_type: Optional event type to count handlers for
            
        Returns:
            Number of handlers
        """
        if event_type:
            return len(self.get_handlers(event_type))
        else:
            return sum(len(handlers) for handlers in self.handlers.values())
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        return {
            "total_handlers": self.get_handler_count(),
            "event_types_covered": len(self.handlers),
            "named_handlers": len(self.named_handlers),
            "handler_details": self.handler_stats
        }
    
    def cleanup_dead_references(self):
        """Clean up dead weak references."""
        for event_type in list(self.handlers.keys()):
            # WeakSet automatically removes dead references
            if not self.handlers[event_type]:
                del self.handlers[event_type]
        
        logger.debug("🧹 CLEANUP: Cleaned up dead handler references")


# Utility functions for creating common handler patterns

def create_simple_handler(
    event_types: Set[EventType],
    handler_func: Callable[[GameEvent], Any],
    name: Optional[str] = None
) -> EventHandler:
    """
    Create a simple event handler from a function.
    
    Args:
        event_types: Event types to handle
        handler_func: Function to handle events
        name: Optional handler name
        
    Returns:
        EventHandler instance
    """
    class SimpleHandler(EventHandler):
        def __init__(self):
            super().__init__(event_types)
            self.handler_func = handler_func
            self.name = name or f"SimpleHandler-{id(self)}"
        
        async def _handle_event(self, event: GameEvent) -> Any:
            if asyncio.iscoroutinefunction(self.handler_func):
                return await self.handler_func(event)
            else:
                return self.handler_func(event)
        
        def get_handler_name(self) -> str:
            return self.name
    
    return SimpleHandler()


def create_async_handler(
    event_types: Set[EventType],
    handler_func: Callable[[GameEvent], Any],
    max_concurrent: int = 10,
    name: Optional[str] = None
) -> AsyncEventHandler:
    """
    Create an async event handler from a function.
    
    Args:
        event_types: Event types to handle
        handler_func: Async function to handle events
        max_concurrent: Maximum concurrent executions
        name: Optional handler name
        
    Returns:
        AsyncEventHandler instance
    """
    class AsyncHandler(AsyncEventHandler):
        def __init__(self):
            super().__init__(event_types, max_concurrent)
            self.handler_func = handler_func
            self.name = name or f"AsyncHandler-{id(self)}"
        
        async def _handle_event(self, event: GameEvent) -> Any:
            if asyncio.iscoroutinefunction(self.handler_func):
                return await self.handler_func(event)
            else:
                return self.handler_func(event)
        
        def get_handler_name(self) -> str:
            return self.name
    
    return AsyncHandler()