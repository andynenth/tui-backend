# domain/interfaces/event_publisher.py
"""
Event publisher interface for domain events.
This allows the domain to publish events without knowing about infrastructure.
"""

from abc import ABC, abstractmethod
from typing import List, Type, Callable, Any
from ..events.base import DomainEvent


class EventPublisher(ABC):
    """
    Interface for publishing domain events.
    
    This interface allows the domain to emit events that can be
    handled by infrastructure services (e.g., for broadcasting,
    persistence, or integration).
    """
    
    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """
        Publish a single domain event.
        
        Args:
            event: The domain event to publish
            
        Raises:
            PublishException: If publishing fails
        """
        pass
    
    @abstractmethod
    async def publish_batch(self, events: List[DomainEvent]) -> None:
        """
        Publish multiple domain events atomically.
        
        Args:
            events: List of events to publish
            
        Raises:
            PublishException: If publishing fails
        """
        pass


class EventSubscriber(ABC):
    """
    Interface for subscribing to domain events.
    
    This is typically implemented by application services
    or infrastructure components that need to react to domain events.
    """
    
    @abstractmethod
    def subscribe(
        self,
        event_type: Type[DomainEvent],
        handler: Callable[[DomainEvent], Any]
    ) -> None:
        """
        Subscribe to a specific event type.
        
        Args:
            event_type: The type of event to subscribe to
            handler: Callback function to handle the event
        """
        pass
    
    @abstractmethod
    def unsubscribe(
        self,
        event_type: Type[DomainEvent],
        handler: Callable[[DomainEvent], Any]
    ) -> None:
        """
        Unsubscribe from a specific event type.
        
        Args:
            event_type: The type of event to unsubscribe from
            handler: The handler to remove
        """
        pass


class EventStore(ABC):
    """
    Interface for persisting domain events.
    
    This supports event sourcing patterns where all changes
    are stored as a sequence of events.
    """
    
    @abstractmethod
    async def append(self, event: DomainEvent) -> None:
        """
        Append an event to the event store.
        
        Args:
            event: Event to store
            
        Raises:
            EventStoreException: If append fails
        """
        pass
    
    @abstractmethod
    async def get_events(
        self,
        aggregate_id: str,
        from_version: int = 0
    ) -> List[DomainEvent]:
        """
        Retrieve events for an aggregate.
        
        Args:
            aggregate_id: ID of the aggregate
            from_version: Starting version (inclusive)
            
        Returns:
            List of events in order
            
        Raises:
            EventStoreException: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def get_events_by_type(
        self,
        event_type: Type[DomainEvent],
        limit: int = 100
    ) -> List[DomainEvent]:
        """
        Retrieve events by type.
        
        Args:
            event_type: Type of events to retrieve
            limit: Maximum number of events
            
        Returns:
            List of events of the specified type
            
        Raises:
            EventStoreException: If retrieval fails
        """
        pass


class PublishException(Exception):
    """Raised when event publishing fails."""
    pass


class EventStoreException(Exception):
    """Base exception for event store errors."""
    pass