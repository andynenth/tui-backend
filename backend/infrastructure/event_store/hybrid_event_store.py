"""
Hybrid event store implementation with memory-first access and async persistence.

This event store maintains high performance for active games while providing
persistence for completed games and historical analysis.
"""

import asyncio
from typing import List, Optional, Dict, Any, Callable, Set
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
import json
from enum import Enum

from infrastructure.persistence.base import IPersistenceAdapter
from infrastructure.persistence.hybrid_repository import HybridRepository
from infrastructure.persistence.memory_adapter import MemoryAdapter
from infrastructure.persistence.filesystem_adapter import FilesystemAdapter
from infrastructure.persistence.repository_factory import (
    PersistenceConfig,
    PersistenceBackend,
    CompletionBasedArchivalPolicy,
)


class EventType(Enum):
    """Standard event types for the game system."""

    # Game lifecycle
    GAME_CREATED = "game_created"
    GAME_STARTED = "game_started"
    GAME_COMPLETED = "game_completed"
    GAME_CANCELLED = "game_cancelled"

    # Player actions
    PLAYER_JOINED = "player_joined"
    PLAYER_LEFT = "player_left"
    PLAYER_ACTION = "player_action"

    # State transitions
    PHASE_CHANGED = "phase_changed"
    TURN_CHANGED = "turn_changed"
    SCORE_UPDATED = "score_updated"

    # System events
    CONNECTION_ESTABLISHED = "connection_established"
    CONNECTION_LOST = "connection_lost"
    ERROR_OCCURRED = "error_occurred"


@dataclass
class Event:
    """
    Represents a domain event in the system.

    Events are immutable records of things that have happened.
    """

    id: str
    type: EventType
    aggregate_id: str  # ID of the entity this event belongs to
    aggregate_type: str  # Type of entity (e.g., 'game', 'room')
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: datetime
    sequence_number: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.type.value,
            "aggregate_id": self.aggregate_id,
            "aggregate_type": self.aggregate_type,
            "data": self.data,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "sequence_number": self.sequence_number,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create event from dictionary."""
        return cls(
            id=data["id"],
            type=EventType(data["type"]),
            aggregate_id=data["aggregate_id"],
            aggregate_type=data["aggregate_type"],
            data=data["data"],
            metadata=data["metadata"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            sequence_number=data["sequence_number"],
        )


@dataclass
class EventStream:
    """
    Collection of events for a specific aggregate.

    Represents the complete history of an entity.
    """

    aggregate_id: str
    aggregate_type: str
    events: List[Event]
    version: int  # Current version (equals last event sequence number)
    is_completed: bool = False

    def append(self, event: Event) -> None:
        """Append event to stream."""
        self.events.append(event)
        self.version = event.sequence_number

    def to_dict(self) -> Dict[str, Any]:
        """Convert stream to dictionary."""
        return {
            "aggregate_id": self.aggregate_id,
            "aggregate_type": self.aggregate_type,
            "events": [e.to_dict() for e in self.events],
            "version": self.version,
            "is_completed": self.is_completed,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EventStream":
        """Create stream from dictionary."""
        return cls(
            aggregate_id=data["aggregate_id"],
            aggregate_type=data["aggregate_type"],
            events=[Event.from_dict(e) for e in data["events"]],
            version=data["version"],
            is_completed=data.get("is_completed", False),
        )


class IEventStore:
    """Interface for event store operations."""

    async def append_event(self, event: Event) -> None:
        """Append a single event to the store."""
        raise NotImplementedError

    async def append_events(self, events: List[Event]) -> None:
        """Append multiple events atomically."""
        raise NotImplementedError

    async def get_events(
        self,
        aggregate_id: str,
        from_version: Optional[int] = None,
        to_version: Optional[int] = None,
    ) -> List[Event]:
        """Get events for an aggregate within version range."""
        raise NotImplementedError

    async def get_stream(self, aggregate_id: str) -> Optional[EventStream]:
        """Get complete event stream for an aggregate."""
        raise NotImplementedError

    async def get_all_events(
        self,
        event_type: Optional[EventType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Event]:
        """Get all events matching criteria."""
        raise NotImplementedError


class HybridEventStore(IEventStore):
    """
    High-performance event store with memory-first access and async persistence.

    Features:
    - In-memory storage for active game events (microsecond access)
    - Async persistence for completed games
    - Event replay capabilities
    - Subscription support for real-time processing
    - Automatic archival of old events
    """

    def __init__(
        self,
        memory_capacity: int = 100000,
        archive_completed_games: bool = True,
        archive_after_hours: int = 24,
        enable_snapshots: bool = True,
        snapshot_frequency: int = 100,
    ):
        """
        Initialize hybrid event store.

        Args:
            memory_capacity: Maximum events to keep in memory
            archive_completed_games: Whether to archive completed game events
            archive_after_hours: Hours before archiving inactive streams
            enable_snapshots: Whether to create snapshots for faster replay
            snapshot_frequency: Events between snapshots
        """
        # Memory storage
        self._streams: Dict[str, EventStream] = {}
        self._events_by_type: Dict[EventType, deque] = defaultdict(deque)
        self._global_sequence = 0

        # Configuration
        self._memory_capacity = memory_capacity
        self._archive_completed_games = archive_completed_games
        self._archive_after = timedelta(hours=archive_after_hours)
        self._enable_snapshots = enable_snapshots
        self._snapshot_frequency = snapshot_frequency

        # Persistence setup
        self._setup_persistence()

        # Subscriptions
        self._subscribers: Dict[EventType, List[Callable]] = defaultdict(list)

        # Background tasks
        self._archive_task: Optional[asyncio.Task] = None

        # Metrics
        self._metrics = {
            "events_appended": 0,
            "events_replayed": 0,
            "streams_archived": 0,
            "snapshots_created": 0,
        }

        # Lock for thread safety
        self._lock = asyncio.Lock()

    def _setup_persistence(self):
        """Set up persistence layer."""
        # Memory adapter for fast access
        memory_config = PersistenceConfig(
            backend=PersistenceBackend.MEMORY,
            options={
                "max_items": self._memory_capacity // 10,  # Streams, not events
                "enable_archives": True,
            },
        )
        memory_adapter = MemoryAdapter[EventStream](memory_config)

        # Filesystem adapter for persistence
        filesystem_config = PersistenceConfig(
            backend=PersistenceBackend.FILESYSTEM,
            options={
                "base_path": "./data/event_store",
                "archive_path": "./data/event_archives",
                "index_fields": ["aggregate_type", "is_completed"],
            },
        )
        filesystem_adapter = FilesystemAdapter[EventStream](filesystem_config)

        # Hybrid repository with completion-based archival
        self._repository = HybridRepository(
            memory_adapter=memory_adapter,
            persistent_adapter=filesystem_adapter,
            archival_policy=CompletionBasedArchivalPolicy("is_completed"),
            archive_interval=300,  # 5 minutes
        )

    async def start(self) -> None:
        """Start background processes."""
        await self._repository.start()

        if not self._archive_task:
            self._archive_task = asyncio.create_task(self._archive_worker())

    async def stop(self) -> None:
        """Stop background processes."""
        await self._repository.stop()

        if self._archive_task:
            self._archive_task.cancel()
            try:
                await self._archive_task
            except asyncio.CancelledError:
                pass

    # IEventStore implementation

    async def append_event(self, event: Event) -> None:
        """Append a single event to the store."""
        await self.append_events([event])

    async def append_events(self, events: List[Event]) -> None:
        """Append multiple events atomically."""
        async with self._lock:
            for event in events:
                # Assign sequence number
                self._global_sequence += 1
                event.sequence_number = self._global_sequence

                # Get or create stream
                stream_key = f"{event.aggregate_type}:{event.aggregate_id}"
                if stream_key not in self._streams:
                    self._streams[stream_key] = EventStream(
                        aggregate_id=event.aggregate_id,
                        aggregate_type=event.aggregate_type,
                        events=[],
                        version=0,
                    )

                stream = self._streams[stream_key]
                stream.append(event)

                # Add to type index
                self._events_by_type[event.type].append(event)

                # Check if stream should be marked as completed
                if event.type == EventType.GAME_COMPLETED:
                    stream.is_completed = True

                # Update metrics
                self._metrics["events_appended"] += 1

                # Notify subscribers
                await self._notify_subscribers(event)

            # Save updated streams
            for event in events:
                stream_key = f"{event.aggregate_type}:{event.aggregate_id}"
                stream = self._streams[stream_key]
                await self._repository.save(stream_key, stream)

            # Check memory capacity
            await self._check_memory_capacity()

    async def get_events(
        self,
        aggregate_id: str,
        from_version: Optional[int] = None,
        to_version: Optional[int] = None,
    ) -> List[Event]:
        """Get events for an aggregate within version range."""
        # Try memory first
        for stream_key, stream in self._streams.items():
            if stream.aggregate_id == aggregate_id:
                events = stream.events

                # Apply version filter
                if from_version is not None:
                    events = [e for e in events if e.sequence_number >= from_version]
                if to_version is not None:
                    events = [e for e in events if e.sequence_number <= to_version]

                self._metrics["events_replayed"] += len(events)
                return events

        # Try persistent storage
        # Search all possible stream keys (we don't know the aggregate type)
        for aggregate_type in ["game", "room", "player"]:
            stream_key = f"{aggregate_type}:{aggregate_id}"
            stream = await self._repository.get(stream_key)

            if stream:
                events = stream.events

                # Apply version filter
                if from_version is not None:
                    events = [e for e in events if e.sequence_number >= from_version]
                if to_version is not None:
                    events = [e for e in events if e.sequence_number <= to_version]

                self._metrics["events_replayed"] += len(events)
                return events

        return []

    async def get_stream(self, aggregate_id: str) -> Optional[EventStream]:
        """Get complete event stream for an aggregate."""
        # Try memory first
        for stream_key, stream in self._streams.items():
            if stream.aggregate_id == aggregate_id:
                return stream

        # Try persistent storage
        for aggregate_type in ["game", "room", "player"]:
            stream_key = f"{aggregate_type}:{aggregate_id}"
            stream = await self._repository.get(stream_key)
            if stream:
                return stream

        return None

    async def get_all_events(
        self,
        event_type: Optional[EventType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Event]:
        """Get all events matching criteria."""
        events = []

        # Get from memory
        if event_type:
            # Use type index
            type_events = list(self._events_by_type.get(event_type, []))
        else:
            # Get all events from all streams
            type_events = []
            for stream in self._streams.values():
                type_events.extend(stream.events)

        # Apply time filter
        for event in type_events:
            if start_time and event.timestamp < start_time:
                continue
            if end_time and event.timestamp > end_time:
                continue
            events.append(event)

        # Sort by sequence number
        events.sort(key=lambda e: e.sequence_number)

        self._metrics["events_replayed"] += len(events)
        return events

    # Subscription support

    def subscribe(self, event_type: EventType, handler: Callable) -> None:
        """Subscribe to events of a specific type."""
        self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: EventType, handler: Callable) -> None:
        """Unsubscribe from events."""
        if handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)

    async def _notify_subscribers(self, event: Event) -> None:
        """Notify subscribers of new event."""
        handlers = self._subscribers.get(event.type, [])

        # Run handlers concurrently
        if handlers:
            await asyncio.gather(
                *[handler(event) for handler in handlers], return_exceptions=True
            )

    # Memory management

    async def _check_memory_capacity(self) -> None:
        """Check and manage memory capacity."""
        total_events = sum(len(stream.events) for stream in self._streams.values())

        if total_events > self._memory_capacity:
            # Find oldest completed streams to evict
            completed_streams = [
                (key, stream)
                for key, stream in self._streams.items()
                if stream.is_completed
            ]

            # Sort by last event timestamp
            completed_streams.sort(
                key=lambda x: x[1].events[-1].timestamp if x[1].events else datetime.min
            )

            # Evict oldest completed streams
            evicted = 0
            for key, stream in completed_streams:
                if total_events - evicted <= self._memory_capacity * 0.8:
                    break

                # Archive if needed
                if self._archive_completed_games:
                    await self._repository.archive_now(key)

                # Remove from memory
                del self._streams[key]

                # Remove from type index
                for event in stream.events:
                    if event in self._events_by_type[event.type]:
                        self._events_by_type[event.type].remove(event)

                evicted += len(stream.events)

    async def _archive_worker(self) -> None:
        """Background worker for archiving old streams."""
        while True:
            try:
                await asyncio.sleep(3600)  # Check hourly

                now = datetime.utcnow()
                streams_to_archive = []

                # Find inactive streams
                for key, stream in self._streams.items():
                    if not stream.events:
                        continue

                    last_event_time = stream.events[-1].timestamp
                    if now - last_event_time > self._archive_after:
                        streams_to_archive.append(key)

                # Archive inactive streams
                for key in streams_to_archive:
                    await self._repository.archive_now(key)
                    self._metrics["streams_archived"] += 1

            except asyncio.CancelledError:
                break
            except Exception:
                # Log error and continue
                await asyncio.sleep(60)

    # Snapshot support

    async def create_snapshot(self, aggregate_id: str) -> Dict[str, Any]:
        """Create a snapshot of current aggregate state."""
        stream = await self.get_stream(aggregate_id)
        if not stream:
            return {}

        # This would be customized based on aggregate type
        # For now, return basic info
        snapshot = {
            "aggregate_id": aggregate_id,
            "aggregate_type": stream.aggregate_type,
            "version": stream.version,
            "event_count": len(stream.events),
            "created_at": datetime.utcnow().isoformat(),
        }

        self._metrics["snapshots_created"] += 1
        return snapshot

    # Metrics and monitoring

    async def get_metrics(self) -> Dict[str, Any]:
        """Get event store metrics."""
        repo_metrics = await self._repository.get_metrics()

        return {
            "store_metrics": dict(self._metrics),
            "total_streams": len(self._streams),
            "total_events": sum(len(s.events) for s in self._streams.values()),
            "completed_streams": sum(
                1 for s in self._streams.values() if s.is_completed
            ),
            "repository_metrics": repo_metrics,
            "subscribers": {
                event_type.value: len(handlers)
                for event_type, handlers in self._subscribers.items()
            },
        }
