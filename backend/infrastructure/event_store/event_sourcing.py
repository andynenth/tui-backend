"""
Event sourcing abstractions and base classes.

This module provides the foundation for implementing event-sourced
aggregates and projections in the game system.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Type, TypeVar, Generic, Callable
from datetime import datetime
import uuid

from .hybrid_event_store import Event, EventType, IEventStore, EventStream


T = TypeVar("T", bound="EventSourcedAggregate")


class DomainEvent:
    """Base class for domain events."""

    def __init__(self, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        self.data = data
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()

    @property
    @abstractmethod
    def event_type(self) -> EventType:
        """Get the event type."""
        pass

    def to_event(
        self, aggregate_id: str, aggregate_type: str, sequence_number: int = 0
    ) -> Event:
        """Convert domain event to storage event."""
        return Event(
            id=str(uuid.uuid4()),
            type=self.event_type,
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            data=self.data,
            metadata=self.metadata,
            timestamp=self.timestamp,
            sequence_number=sequence_number,
        )


class EventSourcedAggregate(ABC):
    """
    Base class for event-sourced aggregates.

    Aggregates are rebuilt from their event history and produce
    new events when commands are executed.
    """

    def __init__(self, aggregate_id: Optional[str] = None):
        self.id = aggregate_id or str(uuid.uuid4())
        self.version = 0
        self._uncommitted_events: List[DomainEvent] = []
        self._event_handlers: Dict[EventType, Callable] = {}

        # Register event handlers
        self._register_event_handlers()

    @property
    @abstractmethod
    def aggregate_type(self) -> str:
        """Get the aggregate type name."""
        pass

    @abstractmethod
    def _register_event_handlers(self) -> None:
        """Register event handlers for rebuilding state."""
        pass

    def apply_event(self, event: Event) -> None:
        """Apply a historical event to rebuild state."""
        handler = self._event_handlers.get(event.type)
        if handler:
            handler(event)
        self.version = event.sequence_number

    def raise_event(self, domain_event: DomainEvent) -> None:
        """Raise a new domain event."""
        # Apply to current state
        event = domain_event.to_event(self.id, self.aggregate_type, self.version + 1)
        self.apply_event(event)

        # Add to uncommitted events
        self._uncommitted_events.append(domain_event)

    def get_uncommitted_events(self) -> List[DomainEvent]:
        """Get events that haven't been persisted yet."""
        return self._uncommitted_events.copy()

    def mark_events_committed(self) -> None:
        """Mark all uncommitted events as committed."""
        self._uncommitted_events.clear()

    @classmethod
    def from_events(cls: Type[T], events: List[Event]) -> T:
        """Rebuild aggregate from event history."""
        if not events:
            raise ValueError("Cannot rebuild aggregate from empty event list")

        # Create instance with the aggregate ID
        instance = cls(events[0].aggregate_id)

        # Apply all events
        for event in events:
            instance.apply_event(event)

        return instance


class EventSourcedRepository(Generic[T], ABC):
    """
    Repository for event-sourced aggregates.

    Handles loading aggregates from events and saving new events.
    """

    def __init__(self, event_store: IEventStore, aggregate_class: Type[T]):
        self._event_store = event_store
        self._aggregate_class = aggregate_class

    async def get(self, aggregate_id: str) -> Optional[T]:
        """Load aggregate by ID."""
        events = await self._event_store.get_events(aggregate_id)

        if not events:
            return None

        return self._aggregate_class.from_events(events)

    async def save(self, aggregate: T) -> None:
        """Save aggregate by persisting its uncommitted events."""
        uncommitted = aggregate.get_uncommitted_events()

        if not uncommitted:
            return

        # Convert to storage events
        events = [
            event.to_event(
                aggregate.id, aggregate.aggregate_type, aggregate.version + i + 1
            )
            for i, event in enumerate(uncommitted)
        ]

        # Persist events
        await self._event_store.append_events(events)

        # Mark as committed
        aggregate.mark_events_committed()

    async def exists(self, aggregate_id: str) -> bool:
        """Check if aggregate exists."""
        stream = await self._event_store.get_stream(aggregate_id)
        return stream is not None


class Projection(ABC):
    """
    Base class for projections that build read models from events.

    Projections listen to events and update denormalized views
    for efficient querying.
    """

    def __init__(self, name: str):
        self.name = name
        self._handlers: Dict[EventType, Callable] = {}
        self._last_processed_sequence = 0

        # Register handlers
        self._register_handlers()

    @abstractmethod
    def _register_handlers(self) -> None:
        """Register event handlers for projection updates."""
        pass

    def register_handler(self, event_type: EventType, handler: Callable) -> None:
        """Register a handler for an event type."""
        self._handlers[event_type] = handler

    async def handle_event(self, event: Event) -> None:
        """Handle a single event."""
        handler = self._handlers.get(event.type)
        if handler:
            await handler(event)

        self._last_processed_sequence = max(
            self._last_processed_sequence, event.sequence_number
        )

    async def rebuild_from_events(self, events: List[Event]) -> None:
        """Rebuild projection from event history."""
        # Clear current state
        await self.clear()

        # Process all events
        for event in sorted(events, key=lambda e: e.sequence_number):
            await self.handle_event(event)

    @abstractmethod
    async def clear(self) -> None:
        """Clear projection state."""
        pass

    def get_last_processed_sequence(self) -> int:
        """Get the sequence number of the last processed event."""
        return self._last_processed_sequence


class ProjectionManager:
    """
    Manages multiple projections and keeps them synchronized with events.

    Can run projections in real-time or catch up from history.
    """

    def __init__(self, event_store: IEventStore):
        self._event_store = event_store
        self._projections: Dict[str, Projection] = {}
        self._running = False

    def register_projection(self, projection: Projection) -> None:
        """Register a projection."""
        self._projections[projection.name] = projection

    async def rebuild_all(self) -> None:
        """Rebuild all projections from event history."""
        # Get all events
        all_events = await self._event_store.get_all_events()

        # Rebuild each projection
        for projection in self._projections.values():
            await projection.rebuild_from_events(all_events)

    async def catch_up(self, projection_name: str) -> None:
        """Catch up a specific projection to current state."""
        projection = self._projections.get(projection_name)
        if not projection:
            return

        # Get events after last processed
        all_events = await self._event_store.get_all_events()
        new_events = [
            e
            for e in all_events
            if e.sequence_number > projection.get_last_processed_sequence()
        ]

        # Process new events
        for event in new_events:
            await projection.handle_event(event)

    async def start_live_projections(self) -> None:
        """Start processing events in real-time."""
        self._running = True

        # Subscribe to all event types
        for event_type in EventType:
            self._event_store.subscribe(
                event_type, lambda e: asyncio.create_task(self._handle_live_event(e))
            )

    async def stop_live_projections(self) -> None:
        """Stop processing events in real-time."""
        self._running = False

        # Unsubscribe from all event types
        for event_type in EventType:
            # Note: Would need to store handler references for proper cleanup
            pass

    async def _handle_live_event(self, event: Event) -> None:
        """Handle a live event by updating all projections."""
        if not self._running:
            return

        # Update all projections concurrently
        tasks = [
            projection.handle_event(event) for projection in self._projections.values()
        ]

        await asyncio.gather(*tasks, return_exceptions=True)


# Example domain events for the game system


class GameCreatedEvent(DomainEvent):
    """Event raised when a game is created."""

    event_type = EventType.GAME_CREATED

    def __init__(self, room_id: str, players: List[str], config: Dict[str, Any]):
        super().__init__({"room_id": room_id, "players": players, "config": config})


class GameStartedEvent(DomainEvent):
    """Event raised when a game starts."""

    event_type = EventType.GAME_STARTED

    def __init__(self, started_by: str):
        super().__init__(
            {"started_by": started_by, "started_at": datetime.utcnow().isoformat()}
        )


class PlayerActionEvent(DomainEvent):
    """Event raised when a player takes an action."""

    event_type = EventType.PLAYER_ACTION

    def __init__(self, player_id: str, action_type: str, action_data: Dict[str, Any]):
        super().__init__(
            {
                "player_id": player_id,
                "action_type": action_type,
                "action_data": action_data,
            }
        )


class PhaseChangedEvent(DomainEvent):
    """Event raised when game phase changes."""

    event_type = EventType.PHASE_CHANGED

    def __init__(self, from_phase: str, to_phase: str, phase_data: Dict[str, Any]):
        super().__init__(
            {"from_phase": from_phase, "to_phase": to_phase, "phase_data": phase_data}
        )
