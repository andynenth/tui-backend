"""
Event sourcing implementation for state machine persistence.

Provides full event-sourced state machine functionality with projections.
"""

from typing import Dict, Any, Optional, List, Callable, Type, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import asyncio
from collections import defaultdict
import logging
from abc import ABC, abstractmethod
import uuid

from .abstractions import (
    IStatePersistence,
    IStateTransitionLog,
    StateTransition,
    PersistedState,
    StateVersion,
)
from .transition_log import StateTransitionLogger


logger = logging.getLogger(__name__)


class StateEventType(Enum):
    """Types of state machine events."""

    CREATED = "created"
    TRANSITIONED = "transitioned"
    UPDATED = "updated"
    SNAPSHOT_CREATED = "snapshot_created"
    RESTORED = "restored"
    DELETED = "deleted"
    ERROR = "error"


@dataclass
class StateEvent:
    """An event in the state machine's lifecycle."""

    event_id: str
    state_machine_id: str
    event_type: StateEventType
    event_data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    sequence_number: int = 0
    actor_id: Optional[str] = None
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_id": self.event_id,
            "state_machine_id": self.state_machine_id,
            "event_type": self.event_type.value,
            "event_data": self.event_data,
            "timestamp": self.timestamp.isoformat(),
            "sequence_number": self.sequence_number,
            "actor_id": self.actor_id,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StateEvent":
        """Create from dictionary."""
        return cls(
            event_id=data["event_id"],
            state_machine_id=data["state_machine_id"],
            event_type=StateEventType(data["event_type"]),
            event_data=data["event_data"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            sequence_number=data["sequence_number"],
            actor_id=data.get("actor_id"),
            correlation_id=data.get("correlation_id"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class EventStream:
    """A stream of events for a state machine."""

    state_machine_id: str
    events: List[StateEvent] = field(default_factory=list)
    version: int = 0
    last_snapshot_version: int = 0

    def append(self, event: StateEvent) -> None:
        """Append an event to the stream."""
        self.events.append(event)
        self.version = event.sequence_number

    def events_since(self, version: int) -> List[StateEvent]:
        """Get events since a specific version."""
        return [e for e in self.events if e.sequence_number > version]


class StateProjection(ABC):
    """Base class for state projections."""

    @abstractmethod
    def apply_event(self, event: StateEvent, state: Dict[str, Any]) -> Dict[str, Any]:
        """Apply an event to the current state."""
        pass

    @abstractmethod
    def can_handle(self, event: StateEvent) -> bool:
        """Check if this projection can handle the event."""
        pass


class DefaultStateProjection(StateProjection):
    """Default projection that handles standard state events."""

    def apply_event(self, event: StateEvent, state: Dict[str, Any]) -> Dict[str, Any]:
        """Apply event to state."""
        new_state = state.copy()

        if event.event_type == StateEventType.CREATED:
            new_state.update(event.event_data)
            new_state["created_at"] = event.timestamp.isoformat()

        elif event.event_type == StateEventType.TRANSITIONED:
            new_state["current_state"] = event.event_data.get("to_state")
            new_state["last_transition"] = event.event_data
            new_state["last_updated"] = event.timestamp.isoformat()

            # Update state data with transition payload
            if "state_data" not in new_state:
                new_state["state_data"] = {}
            new_state["state_data"].update(event.event_data.get("payload", {}))

        elif event.event_type == StateEventType.UPDATED:
            if "state_data" not in new_state:
                new_state["state_data"] = {}
            new_state["state_data"].update(event.event_data)
            new_state["last_updated"] = event.timestamp.isoformat()

        elif event.event_type == StateEventType.RESTORED:
            new_state.update(event.event_data.get("restored_state", {}))
            new_state["restored_at"] = event.timestamp.isoformat()

        return new_state

    def can_handle(self, event: StateEvent) -> bool:
        """Check if this projection can handle the event."""
        return event.event_type in (
            StateEventType.CREATED,
            StateEventType.TRANSITIONED,
            StateEventType.UPDATED,
            StateEventType.RESTORED,
        )


class EventStore(ABC):
    """Abstract event store interface."""

    @abstractmethod
    async def append_event(self, event: StateEvent) -> None:
        """Append an event to the store."""
        pass

    @abstractmethod
    async def get_events(
        self,
        state_machine_id: str,
        from_sequence: int = 0,
        to_sequence: Optional[int] = None,
    ) -> List[StateEvent]:
        """Get events for a state machine."""
        pass

    @abstractmethod
    async def get_latest_sequence(self, state_machine_id: str) -> int:
        """Get the latest sequence number."""
        pass


class InMemoryEventStore(EventStore):
    """In-memory event store implementation."""

    def __init__(self, max_events_per_stream: int = 10000):
        """Initialize in-memory store."""
        self.max_events = max_events_per_stream
        self._streams: Dict[str, EventStream] = {}
        self._global_sequence = 0
        self._lock = asyncio.Lock()

    async def append_event(self, event: StateEvent) -> None:
        """Append an event to the store."""
        async with self._lock:
            # Assign sequence number
            self._global_sequence += 1
            event.sequence_number = self._global_sequence

            # Get or create stream
            if event.state_machine_id not in self._streams:
                self._streams[event.state_machine_id] = EventStream(
                    state_machine_id=event.state_machine_id
                )

            stream = self._streams[event.state_machine_id]
            stream.append(event)

            # Enforce limits
            if len(stream.events) > self.max_events:
                # Remove oldest events
                stream.events = stream.events[-self.max_events :]

            logger.debug(
                f"Appended event {event.event_id} to stream {event.state_machine_id}"
            )

    async def get_events(
        self,
        state_machine_id: str,
        from_sequence: int = 0,
        to_sequence: Optional[int] = None,
    ) -> List[StateEvent]:
        """Get events for a state machine."""
        async with self._lock:
            stream = self._streams.get(state_machine_id)
            if not stream:
                return []

            events = stream.events_since(from_sequence)

            if to_sequence is not None:
                events = [e for e in events if e.sequence_number <= to_sequence]

            return events

    async def get_latest_sequence(self, state_machine_id: str) -> int:
        """Get the latest sequence number."""
        async with self._lock:
            stream = self._streams.get(state_machine_id)
            return stream.version if stream else 0


class StateMachineEventStore:
    """
    Event store for state machines with projection support.

    Features:
    - Event sourcing
    - Multiple projections
    - Snapshot optimization
    - Event replay
    """

    def __init__(
        self,
        event_store: EventStore,
        projections: Optional[List[StateProjection]] = None,
        snapshot_frequency: int = 100,
    ):
        """Initialize event store."""
        self.event_store = event_store
        self.projections = projections or [DefaultStateProjection()]
        self.snapshot_frequency = snapshot_frequency
        self._event_handlers: Dict[StateEventType, List[Callable]] = defaultdict(list)

    def register_handler(
        self, event_type: StateEventType, handler: Callable[[StateEvent], None]
    ) -> None:
        """Register an event handler."""
        self._event_handlers[event_type].append(handler)

    async def append_event(
        self,
        state_machine_id: str,
        event_type: StateEventType,
        event_data: Dict[str, Any],
        actor_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> StateEvent:
        """Append an event to the store."""
        # Create event
        event = StateEvent(
            event_id=str(uuid.uuid4()),
            state_machine_id=state_machine_id,
            event_type=event_type,
            event_data=event_data,
            actor_id=actor_id,
            correlation_id=correlation_id,
        )

        # Store event
        await self.event_store.append_event(event)

        # Notify handlers
        for handler in self._event_handlers[event_type]:
            try:
                await asyncio.create_task(handler(event))
            except Exception as e:
                logger.error(f"Error in event handler: {e}")

        return event

    async def get_current_state(
        self, state_machine_id: str, from_version: int = 0
    ) -> Dict[str, Any]:
        """Get current state by replaying events."""
        # Get events
        events = await self.event_store.get_events(
            state_machine_id, from_sequence=from_version
        )

        # Apply events through projections
        state = {}
        for event in events:
            for projection in self.projections:
                if projection.can_handle(event):
                    state = projection.apply_event(event, state)

        return state

    async def get_state_at_version(
        self, state_machine_id: str, version: int
    ) -> Dict[str, Any]:
        """Get state at a specific version."""
        # Get events up to version
        events = await self.event_store.get_events(
            state_machine_id, from_sequence=0, to_sequence=version
        )

        # Apply events
        state = {}
        for event in events:
            for projection in self.projections:
                if projection.can_handle(event):
                    state = projection.apply_event(event, state)

        return state

    async def create_state_machine(
        self,
        state_machine_id: str,
        initial_state: Dict[str, Any],
        actor_id: Optional[str] = None,
    ) -> StateEvent:
        """Create a new state machine."""
        return await self.append_event(
            state_machine_id=state_machine_id,
            event_type=StateEventType.CREATED,
            event_data=initial_state,
            actor_id=actor_id,
        )

    async def transition_state(
        self, state_machine_id: str, transition: StateTransition
    ) -> StateEvent:
        """Record a state transition."""
        return await self.append_event(
            state_machine_id=state_machine_id,
            event_type=StateEventType.TRANSITIONED,
            event_data=transition.to_dict(),
            actor_id=transition.actor_id,
        )

    async def update_state(
        self,
        state_machine_id: str,
        updates: Dict[str, Any],
        actor_id: Optional[str] = None,
    ) -> StateEvent:
        """Update state data."""
        return await self.append_event(
            state_machine_id=state_machine_id,
            event_type=StateEventType.UPDATED,
            event_data=updates,
            actor_id=actor_id,
        )

    async def get_event_history(
        self, state_machine_id: str, limit: Optional[int] = None
    ) -> List[StateEvent]:
        """Get event history for a state machine."""
        events = await self.event_store.get_events(state_machine_id)

        if limit:
            events = events[-limit:]

        return events

    async def get_state_version(self, state_machine_id: str) -> int:
        """Get current version of state machine."""
        return await self.event_store.get_latest_sequence(state_machine_id)


class EventSourcedStateMachine(IStatePersistence):
    """
    Event-sourced state machine implementation.

    Features:
    - Full event sourcing
    - Automatic snapshots
    - State reconstruction
    """

    def __init__(
        self,
        event_store: StateMachineEventStore,
        transition_logger: Optional[StateTransitionLogger] = None,
    ):
        """Initialize event-sourced state machine."""
        super().__init__()
        self.event_store = event_store
        self.transition_logger = transition_logger
        self._state_cache: Dict[str, Dict[str, Any]] = {}

    async def save_state(
        self,
        state_machine_id: str,
        state: Dict[str, Any],
        version: Optional[StateVersion] = None,
    ) -> str:
        """Save state by creating events."""
        # Check if this is a new state machine
        current_version = await self.event_store.get_state_version(state_machine_id)

        if current_version == 0:
            # Create new state machine
            await self.event_store.create_state_machine(state_machine_id, state)
        else:
            # Update existing state machine
            await self.event_store.update_state(state_machine_id, state)

        # Update cache
        self._state_cache[state_machine_id] = state

        return f"event_{state_machine_id}_{current_version + 1}"

    async def load_state(
        self, state_machine_id: str, version: Optional[StateVersion] = None
    ) -> Optional[PersistedState]:
        """Load state by replaying events."""
        # Check cache first
        if not version and state_machine_id in self._state_cache:
            cached_state = self._state_cache[state_machine_id]
            return self._create_persisted_state(state_machine_id, cached_state)

        # Get state from event store
        if version:
            # Get state at specific version
            version_number = version.major * 10000 + version.minor * 100 + version.patch
            state = await self.event_store.get_state_at_version(
                state_machine_id, version_number
            )
        else:
            # Get current state
            state = await self.event_store.get_current_state(state_machine_id)

        if not state:
            return None

        # Cache current state
        if not version:
            self._state_cache[state_machine_id] = state

        return self._create_persisted_state(state_machine_id, state)

    async def delete_state(self, state_machine_id: str) -> bool:
        """Delete state by marking as deleted."""
        # Record deletion event
        await self.event_store.append_event(
            state_machine_id,
            StateEventType.DELETED,
            {"deleted_at": datetime.utcnow().isoformat()},
        )

        # Remove from cache
        self._state_cache.pop(state_machine_id, None)

        return True

    async def list_versions(self, state_machine_id: str) -> List[StateVersion]:
        """List available versions."""
        # Get all events
        events = await self.event_store.get_event_history(state_machine_id)

        # Create versions for significant events
        versions = []
        for event in events:
            if event.event_type in (
                StateEventType.CREATED,
                StateEventType.SNAPSHOT_CREATED,
                StateEventType.RESTORED,
            ):
                version = StateVersion(
                    major=1,
                    minor=0,
                    patch=event.sequence_number,
                    timestamp=event.timestamp,
                )
                versions.append(version)

        return versions

    def _create_persisted_state(
        self, state_machine_id: str, state: Dict[str, Any]
    ) -> PersistedState:
        """Create persisted state from event-sourced state."""
        return PersistedState(
            state_machine_id=state_machine_id,
            state_type=state.get("state_type", "event_sourced"),
            current_state=state.get("current_state", "unknown"),
            state_data=state,
            version=StateVersion(1, 0, 0),
            created_at=datetime.fromisoformat(
                state.get("created_at", datetime.utcnow().isoformat())
            ),
            updated_at=datetime.fromisoformat(
                state.get("last_updated", datetime.utcnow().isoformat())
            ),
            metadata={"source": "event_store"},
        )


class StateRehydrator:
    """
    Rehydrates state machines from events.

    Features:
    - Efficient state reconstruction
    - Parallel rehydration
    - Progress tracking
    """

    def __init__(self, event_store: StateMachineEventStore, batch_size: int = 100):
        """Initialize rehydrator."""
        self.event_store = event_store
        self.batch_size = batch_size

    async def rehydrate_state(
        self, state_machine_id: str, target_version: Optional[int] = None
    ) -> Dict[str, Any]:
        """Rehydrate a single state machine."""
        if target_version:
            return await self.event_store.get_state_at_version(
                state_machine_id, target_version
            )
        else:
            return await self.event_store.get_current_state(state_machine_id)

    async def rehydrate_multiple(
        self,
        state_machine_ids: List[str],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Rehydrate multiple state machines."""
        results = {}
        total = len(state_machine_ids)

        # Process in batches
        for i in range(0, total, self.batch_size):
            batch = state_machine_ids[i : i + self.batch_size]

            # Rehydrate batch in parallel
            tasks = [self.rehydrate_state(sm_id) for sm_id in batch]

            states = await asyncio.gather(*tasks, return_exceptions=True)

            # Store results
            for sm_id, state in zip(batch, states):
                if isinstance(state, Exception):
                    logger.error(f"Error rehydrating {sm_id}: {state}")
                    results[sm_id] = {}
                else:
                    results[sm_id] = state

            # Report progress
            if progress_callback:
                progress_callback(min(i + self.batch_size, total), total)

        return results

    async def validate_state_integrity(self, state_machine_id: str) -> bool:
        """Validate state integrity by checking event consistency."""
        try:
            # Get all events
            events = await self.event_store.get_event_history(state_machine_id)

            # Check sequence numbers
            expected_seq = 1
            for event in events:
                if event.sequence_number != expected_seq:
                    logger.error(
                        f"Sequence gap detected: expected {expected_seq}, "
                        f"got {event.sequence_number}"
                    )
                    return False
                expected_seq += 1

            # Try to rehydrate
            state = await self.rehydrate_state(state_machine_id)

            # Basic validation
            return bool(state)

        except Exception as e:
            logger.error(f"Integrity check failed: {e}")
            return False
