# infrastructure/events/event_store_adapter.py
"""
Adapter for event store that integrates with event bus.
"""

import logging
from typing import List, Optional

from domain.interfaces.event_publisher import EventStore
from domain.events.base import DomainEvent
from infrastructure.persistence.event_publisher_impl import InMemoryEventStore
from application.events.event_bus import EventBus

logger = logging.getLogger(__name__)


class EventStoreAdapter(EventStore):
    """
    Event store that publishes events to event bus after storing.
    
    This ensures that events are persisted before being published,
    providing better reliability.
    """
    
    def __init__(
        self,
        event_store: InMemoryEventStore,
        event_bus: Optional[EventBus] = None
    ):
        """
        Initialize with underlying store and optional event bus.
        
        Args:
            event_store: The actual event store implementation
            event_bus: Optional event bus for publishing stored events
        """
        self._event_store = event_store
        self._event_bus = event_bus
        self._publish_on_store = True
    
    async def append(self, event: DomainEvent) -> None:
        """
        Append event to store and optionally publish.
        
        Args:
            event: Event to store
        """
        # First store the event
        await self._event_store.append(event)
        
        # Then publish if configured
        if self._event_bus and self._publish_on_store:
            try:
                await self._event_bus.publish(event)
            except Exception as e:
                logger.error(
                    f"Failed to publish event after storing: {str(e)}",
                    exc_info=True
                )
                # Don't re-raise - storage succeeded
    
    async def get_events(
        self,
        aggregate_id: str,
        after_version: int = 0
    ) -> List[DomainEvent]:
        """
        Get events for aggregate.
        
        Args:
            aggregate_id: ID of aggregate
            after_version: Only get events after this version
            
        Returns:
            List of events
        """
        return await self._event_store.get_events(aggregate_id, after_version)
    
    async def get_all_events(self) -> List[DomainEvent]:
        """Get all events in the store."""
        return await self._event_store.get_all_events()
    
    def enable_publish_on_store(self) -> None:
        """Enable publishing events when stored."""
        self._publish_on_store = True
    
    def disable_publish_on_store(self) -> None:
        """Disable publishing events when stored."""
        self._publish_on_store = False