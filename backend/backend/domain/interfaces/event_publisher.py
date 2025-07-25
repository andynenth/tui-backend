"""
Event publisher interface.

This defines the contract for publishing domain events.
Infrastructure implementations will handle the actual event distribution.
"""

from abc import ABC, abstractmethod
from typing import List, Callable, Awaitable, Type, Optional
from ..events.base import DomainEvent


EventHandler = Callable[[DomainEvent], Awaitable[None]]


class EventPublisher(ABC):
    """
    Interface for publishing domain events.
    
    Implementations might use in-memory event bus, message queues,
    or other mechanisms to distribute events to handlers.
    """
    
    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """
        Publish a domain event.
        
        Args:
            event: The domain event to publish
        """
        pass
    
    @abstractmethod
    async def publish_batch(self, events: List[DomainEvent]) -> None:
        """
        Publish multiple domain events.
        
        Args:
            events: List of domain events to publish
        """
        pass


class EventSubscriber(ABC):
    """
    Interface for subscribing to domain events.
    
    Allows handlers to register interest in specific event types.
    """
    
    @abstractmethod
    def subscribe(
        self,
        event_type: Type[DomainEvent],
        handler: EventHandler,
        priority: int = 0
    ) -> None:
        """
        Subscribe a handler to a specific event type.
        
        Args:
            event_type: The type of event to handle
            handler: The async function to call when event occurs
            priority: Handler priority (higher = called first)
        """
        pass
    
    @abstractmethod
    def unsubscribe(
        self,
        event_type: Type[DomainEvent],
        handler: EventHandler
    ) -> None:
        """
        Unsubscribe a handler from an event type.
        
        Args:
            event_type: The type of event
            handler: The handler to remove
        """
        pass
    
    @abstractmethod
    def get_handlers(self, event_type: Type[DomainEvent]) -> List[EventHandler]:
        """
        Get all handlers for a specific event type.
        
        Args:
            event_type: The type of event
            
        Returns:
            List of handlers sorted by priority
        """
        pass


class EventBus(EventPublisher, EventSubscriber):
    """
    Combined interface for event publishing and subscribing.
    
    Most implementations will support both publishing and subscribing.
    """
    pass


class EventStore(ABC):
    """
    Interface for storing domain events.
    
    Provides event sourcing capabilities.
    """
    
    @abstractmethod
    async def store(self, event: DomainEvent) -> None:
        """Store a single event."""
        pass
    
    @abstractmethod
    async def store_batch(self, events: List[DomainEvent]) -> None:
        """Store multiple events."""
        pass
    
    @abstractmethod
    async def get_events(
        self,
        aggregate_id: str,
        from_sequence: Optional[int] = None,
        to_sequence: Optional[int] = None
    ) -> List[DomainEvent]:
        """
        Retrieve events for an aggregate.
        
        Args:
            aggregate_id: The ID of the aggregate (e.g., room_id)
            from_sequence: Starting sequence number (inclusive)
            to_sequence: Ending sequence number (inclusive)
            
        Returns:
            List of events in order
        """
        pass
    
    @abstractmethod
    async def get_events_by_type(
        self,
        event_type: Type[DomainEvent],
        limit: Optional[int] = None
    ) -> List[DomainEvent]:
        """
        Retrieve events by type.
        
        Args:
            event_type: The type of events to retrieve
            limit: Maximum number of events to return
            
        Returns:
            List of events of the specified type
        """
        pass