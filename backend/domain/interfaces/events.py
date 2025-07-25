"""
Event-related interfaces for the domain layer.

These interfaces define how the domain publishes events
and how infrastructure handles them.
"""

from abc import ABC, abstractmethod
from typing import List, Callable, Optional, Any

from domain.events.base import DomainEvent


class EventPublisher(ABC):
    """
    Interface for publishing domain events.
    
    The infrastructure layer must provide an implementation
    that handles event distribution to interested parties.
    """
    
    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """
        Publish a single domain event.
        
        Args:
            event: Domain event to publish
        """
        pass
    
    @abstractmethod
    async def publish_batch(self, events: List[DomainEvent]) -> None:
        """
        Publish multiple events as a batch.
        
        Args:
            events: List of domain events to publish
        """
        pass


class EventStore(ABC):
    """
    Interface for persisting domain events.
    
    Provides event sourcing capabilities for the domain.
    """
    
    @abstractmethod
    async def append(self, event: DomainEvent) -> None:
        """
        Append an event to the store.
        
        Args:
            event: Event to persist
        """
        pass
    
    @abstractmethod
    async def get_events(
        self,
        aggregate_id: str,
        from_sequence: Optional[int] = None,
        to_sequence: Optional[int] = None
    ) -> List[DomainEvent]:
        """
        Get events for an aggregate.
        
        Args:
            aggregate_id: ID of the aggregate (e.g., room_id)
            from_sequence: Starting sequence number (inclusive)
            to_sequence: Ending sequence number (inclusive)
            
        Returns:
            List of events in sequence order
        """
        pass
    
    @abstractmethod
    async def get_events_by_type(
        self,
        event_type: str,
        limit: int = 100
    ) -> List[DomainEvent]:
        """
        Get events of a specific type.
        
        Args:
            event_type: Type of events to retrieve
            limit: Maximum number of events to return
            
        Returns:
            List of events of the specified type
        """
        pass
    
    @abstractmethod
    async def get_snapshot(
        self,
        aggregate_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get the latest snapshot for an aggregate.
        
        Args:
            aggregate_id: ID of the aggregate
            
        Returns:
            Snapshot data if available, None otherwise
        """
        pass
    
    @abstractmethod
    async def save_snapshot(
        self,
        aggregate_id: str,
        sequence_number: int,
        data: Dict[str, Any]
    ) -> None:
        """
        Save a snapshot of aggregate state.
        
        Args:
            aggregate_id: ID of the aggregate
            sequence_number: Sequence number of last included event
            data: Snapshot data
        """
        pass


class EventHandler(ABC):
    """
    Interface for handling domain events.
    
    Infrastructure components that react to domain events
    should implement this interface.
    """
    
    @abstractmethod
    def can_handle(self, event: DomainEvent) -> bool:
        """
        Check if this handler can process the event.
        
        Args:
            event: Event to check
            
        Returns:
            True if this handler can process the event
        """
        pass
    
    @abstractmethod
    async def handle(self, event: DomainEvent) -> None:
        """
        Handle a domain event.
        
        Args:
            event: Event to handle
        """
        pass
    
    @abstractmethod
    def get_event_types(self) -> List[str]:
        """
        Get list of event types this handler processes.
        
        Returns:
            List of event type names
        """
        pass