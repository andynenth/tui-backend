# infrastructure/persistence/event_publisher_impl.py
"""
Implementation of the EventPublisher interface.
"""

import logging
from typing import List, Dict, Type, Callable, Any
import asyncio
from collections import defaultdict

from domain.interfaces.event_publisher import (
    EventPublisher,
    EventSubscriber,
    EventStore,
    PublishException,
    EventStoreException
)
from domain.events.base import DomainEvent

logger = logging.getLogger(__name__)


class InMemoryEventPublisher(EventPublisher, EventSubscriber):
    """
    In-memory implementation of EventPublisher and EventSubscriber.
    
    This implementation handles event publishing and subscription
    in memory. In production, this might use a message queue.
    """
    
    def __init__(self):
        # Subscribers by event type
        self._subscribers: Dict[Type[DomainEvent], List[Callable]] = defaultdict(list)
        self._publish_lock = asyncio.Lock()
        
        # Stats
        self._published_count = 0
        self._failed_count = 0
    
    async def publish(self, event: DomainEvent) -> None:
        """
        Publish a single domain event.
        
        Args:
            event: The domain event to publish
            
        Raises:
            PublishException: If publishing fails
        """
        async with self._publish_lock:
            try:
                event_type = type(event)
                handlers = self._subscribers.get(event_type, [])
                
                # Also check for base class subscriptions
                for base_type in event_type.__bases__:
                    if issubclass(base_type, DomainEvent):
                        handlers.extend(self._subscribers.get(base_type, []))
                
                # Remove duplicates while preserving order
                seen = set()
                unique_handlers = []
                for handler in handlers:
                    if handler not in seen:
                        seen.add(handler)
                        unique_handlers.append(handler)
                
                # Call all handlers
                for handler in unique_handlers:
                    try:
                        result = handler(event)
                        # Handle both sync and async handlers
                        if asyncio.iscoroutine(result):
                            await result
                    except Exception as e:
                        logger.error(
                            f"Handler {handler.__name__} failed for event {event_type.__name__}: {str(e)}",
                            exc_info=True
                        )
                        # Continue with other handlers
                
                self._published_count += 1
                
                logger.debug(
                    f"Published {event_type.__name__} to {len(unique_handlers)} handlers"
                )
                
            except Exception as e:
                self._failed_count += 1
                raise PublishException(f"Failed to publish event: {str(e)}")
    
    async def publish_batch(self, events: List[DomainEvent]) -> None:
        """
        Publish multiple domain events atomically.
        
        Args:
            events: List of events to publish
            
        Raises:
            PublishException: If publishing fails
        """
        # For in-memory, we just publish each event
        # In production, this might be a transaction
        for event in events:
            await self.publish(event)
    
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
        self._subscribers[event_type].append(handler)
        
        logger.debug(
            f"Subscribed {handler.__name__} to {event_type.__name__}"
        )
    
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
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
                logger.debug(
                    f"Unsubscribed {handler.__name__} from {event_type.__name__}"
                )
            except ValueError:
                # Handler not in list
                pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get publisher statistics."""
        return {
            "published_count": self._published_count,
            "failed_count": self._failed_count,
            "subscriber_count": sum(len(handlers) for handlers in self._subscribers.values()),
            "event_types": list(self._subscribers.keys())
        }


class InMemoryEventStore(EventStore):
    """
    In-memory implementation of EventStore.
    
    This stores events in memory. In production, this would
    use a database for persistence.
    """
    
    def __init__(self):
        # Events by aggregate ID
        self._events: Dict[str, List[DomainEvent]] = defaultdict(list)
        # All events in order
        self._all_events: List[DomainEvent] = []
        self._store_lock = asyncio.Lock()
    
    async def append(self, event: DomainEvent) -> None:
        """
        Append an event to the event store.
        
        Args:
            event: Event to store
            
        Raises:
            EventStoreException: If append fails
        """
        async with self._store_lock:
            try:
                # Store by aggregate ID if available
                if hasattr(event, 'aggregate_id') and event.aggregate_id:
                    self._events[event.aggregate_id].append(event)
                
                # Store in global list
                self._all_events.append(event)
                
                logger.debug(
                    f"Stored {type(event).__name__} "
                    f"(aggregate: {getattr(event, 'aggregate_id', 'N/A')})"
                )
                
            except Exception as e:
                raise EventStoreException(f"Failed to append event: {str(e)}")
    
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
        try:
            events = self._events.get(aggregate_id, [])
            
            # Filter by version if specified
            if from_version > 0:
                events = [
                    e for e in events
                    if hasattr(e, 'version') and e.version >= from_version
                ]
            
            return events
            
        except Exception as e:
            raise EventStoreException(f"Failed to retrieve events: {str(e)}")
    
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
        try:
            matching_events = [
                e for e in self._all_events
                if isinstance(e, event_type)
            ]
            
            # Return most recent events up to limit
            return matching_events[-limit:]
            
        except Exception as e:
            raise EventStoreException(f"Failed to retrieve events by type: {str(e)}")
    
    def get_all_events(self) -> List[DomainEvent]:
        """Get all events (for debugging/testing)."""
        return self._all_events.copy()
    
    def clear(self) -> None:
        """Clear all events (for testing)."""
        self._events.clear()
        self._all_events.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get store statistics."""
        event_type_counts = defaultdict(int)
        for event in self._all_events:
            event_type_counts[type(event).__name__] += 1
        
        return {
            "total_events": len(self._all_events),
            "aggregate_count": len(self._events),
            "event_types": dict(event_type_counts)
        }