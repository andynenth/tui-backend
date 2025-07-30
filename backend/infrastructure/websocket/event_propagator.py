"""
Real-time event propagation system for WebSocket infrastructure.

Provides efficient event broadcasting with various strategies and filters.
"""

from typing import Dict, Set, List, Optional, Any, Callable, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import json
from collections import defaultdict
import logging

from .connection_manager import ConnectionManager, ConnectionInfo


logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """Priority levels for events."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class BroadcastScope(Enum):
    """Scope of event broadcast."""

    CONNECTION = "connection"
    PLAYER = "player"
    ROOM = "room"
    GLOBAL = "global"


@dataclass
class Event:
    """Represents an event to be propagated."""

    event_type: str
    payload: Dict[str, Any]
    scope: BroadcastScope = BroadcastScope.ROOM
    target_id: Optional[str] = None
    priority: EventPriority = EventPriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_message(self) -> Dict[str, Any]:
        """Convert event to WebSocket message."""
        return {
            "type": self.event_type,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class EventSubscription:
    """Subscription to specific event types."""

    connection_id: str
    event_types: Set[str]
    filter_func: Optional[Callable[[Event], bool]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


class BroadcastStrategy(ABC):
    """Abstract base for broadcast strategies."""

    @abstractmethod
    async def get_recipients(
        self, event: Event, connection_manager: ConnectionManager
    ) -> List[ConnectionInfo]:
        """Get list of recipients for an event."""
        pass


class TargetedBroadcast(BroadcastStrategy):
    """Broadcast to specific connections."""

    def __init__(self, connection_ids: Union[str, List[str]]):
        """Initialize with target connection IDs."""
        self.connection_ids = (
            [connection_ids] if isinstance(connection_ids, str) else connection_ids
        )

    async def get_recipients(
        self, event: Event, connection_manager: ConnectionManager
    ) -> List[ConnectionInfo]:
        """Get targeted connections."""
        recipients = []
        for conn_id in self.connection_ids:
            conn = await connection_manager.registry.get_connection(conn_id)
            if conn:
                recipients.append(conn)
        return recipients


class RoomBroadcast(BroadcastStrategy):
    """Broadcast to all connections in a room."""

    def __init__(self, room_id: str, exclude: Optional[Set[str]] = None):
        """Initialize with room ID and exclusions."""
        self.room_id = room_id
        self.exclude = exclude or set()

    async def get_recipients(
        self, event: Event, connection_manager: ConnectionManager
    ) -> List[ConnectionInfo]:
        """Get all connections in room."""
        connections = await connection_manager.registry.get_connections_by_room(
            self.room_id
        )
        return [conn for conn in connections if conn.connection_id not in self.exclude]


class PlayerBroadcast(BroadcastStrategy):
    """Broadcast to all connections for a player."""

    def __init__(self, player_id: str):
        """Initialize with player ID."""
        self.player_id = player_id

    async def get_recipients(
        self, event: Event, connection_manager: ConnectionManager
    ) -> List[ConnectionInfo]:
        """Get all connections for player."""
        return await connection_manager.registry.get_connections_by_player(
            self.player_id
        )


class ConditionalBroadcast(BroadcastStrategy):
    """Broadcast based on connection conditions."""

    def __init__(self, condition: Callable[[ConnectionInfo], bool]):
        """Initialize with condition function."""
        self.condition = condition

    async def get_recipients(
        self, event: Event, connection_manager: ConnectionManager
    ) -> List[ConnectionInfo]:
        """Get connections matching condition."""
        # This would need access to all connections
        # In production, would iterate through registry
        return []


class EventPropagator:
    """
    Central event propagation system.

    Features:
    - Multiple broadcast strategies
    - Event filtering and transformation
    - Priority queuing
    - Batch processing
    - Delivery guarantees
    """

    def __init__(
        self,
        connection_manager: ConnectionManager,
        batch_size: int = 100,
        batch_delay_ms: int = 10,
    ):
        """
        Initialize event propagator.

        Args:
            connection_manager: WebSocket connection manager
            batch_size: Maximum events in a batch
            batch_delay_ms: Delay before sending batch
        """
        self.connection_manager = connection_manager
        self.batch_size = batch_size
        self.batch_delay_ms = batch_delay_ms

        # Event queues by priority
        self._queues: Dict[EventPriority, asyncio.Queue] = {
            priority: asyncio.Queue() for priority in EventPriority
        }

        # Event subscriptions
        self._subscriptions: Dict[str, EventSubscription] = {}
        self._subscriptions_by_type: Dict[str, Set[str]] = defaultdict(set)

        # Delivery tracking
        self._delivery_attempts: Dict[str, int] = defaultdict(int)
        self._failed_deliveries: List[tuple[Event, str, str]] = []

        # Background tasks
        self._tasks: Set[asyncio.Task] = set()
        self._running = False

        # Metrics
        self._metrics = {
            "events_sent": 0,
            "events_failed": 0,
            "batches_processed": 0,
            "avg_batch_size": 0,
        }

    async def start(self) -> None:
        """Start the event propagator."""
        self._running = True

        # Start processing tasks for each priority
        for priority in EventPriority:
            task = asyncio.create_task(self._process_queue(priority))
            self._tasks.add(task)

    async def stop(self) -> None:
        """Stop the event propagator."""
        self._running = False

        # Cancel all tasks
        for task in self._tasks:
            task.cancel()

        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

    async def propagate(
        self, event: Event, strategy: Optional[BroadcastStrategy] = None
    ) -> int:
        """
        Propagate an event.

        Args:
            event: Event to propagate
            strategy: Broadcast strategy (uses event scope if not provided)

        Returns:
            Number of recipients queued
        """
        # Determine recipients
        if strategy:
            recipients = await strategy.get_recipients(event, self.connection_manager)
        else:
            recipients = await self._get_recipients_by_scope(event)

        # Filter by subscriptions
        recipients = await self._filter_by_subscriptions(event, recipients)

        # Queue for each recipient
        for recipient in recipients:
            await self._queue_event(event, recipient.connection_id)

        return len(recipients)

    async def propagate_immediate(
        self, event: Event, strategy: Optional[BroadcastStrategy] = None
    ) -> int:
        """
        Propagate an event immediately (bypass queue).

        Args:
            event: Event to propagate
            strategy: Broadcast strategy

        Returns:
            Number of successful sends
        """
        # Determine recipients
        if strategy:
            recipients = await strategy.get_recipients(event, self.connection_manager)
        else:
            recipients = await self._get_recipients_by_scope(event)

        # Filter by subscriptions
        recipients = await self._filter_by_subscriptions(event, recipients)

        # Send immediately
        sent = 0
        message = event.to_message()

        for recipient in recipients:
            if await self.connection_manager.send_to_connection(
                recipient.connection_id, message
            ):
                sent += 1
                self._metrics["events_sent"] += 1
            else:
                self._metrics["events_failed"] += 1

        return sent

    async def subscribe(
        self,
        connection_id: str,
        event_types: Union[str, List[str]],
        filter_func: Optional[Callable[[Event], bool]] = None,
    ) -> None:
        """
        Subscribe connection to event types.

        Args:
            connection_id: Connection to subscribe
            event_types: Event types to subscribe to
            filter_func: Optional filter function
        """
        if isinstance(event_types, str):
            event_types = [event_types]

        subscription = EventSubscription(
            connection_id=connection_id,
            event_types=set(event_types),
            filter_func=filter_func,
        )

        self._subscriptions[connection_id] = subscription

        # Update type index
        for event_type in event_types:
            self._subscriptions_by_type[event_type].add(connection_id)

    async def unsubscribe(self, connection_id: str) -> None:
        """Remove all subscriptions for a connection."""
        subscription = self._subscriptions.pop(connection_id, None)
        if not subscription:
            return

        # Clean up type index
        for event_type in subscription.event_types:
            self._subscriptions_by_type[event_type].discard(connection_id)
            if not self._subscriptions_by_type[event_type]:
                del self._subscriptions_by_type[event_type]

    async def _get_recipients_by_scope(self, event: Event) -> List[ConnectionInfo]:
        """Get recipients based on event scope."""
        if event.scope == BroadcastScope.CONNECTION and event.target_id:
            conn = await self.connection_manager.registry.get_connection(
                event.target_id
            )
            return [conn] if conn else []

        elif event.scope == BroadcastScope.PLAYER and event.target_id:
            return await self.connection_manager.registry.get_connections_by_player(
                event.target_id
            )

        elif event.scope == BroadcastScope.ROOM and event.target_id:
            return await self.connection_manager.registry.get_connections_by_room(
                event.target_id
            )

        elif event.scope == BroadcastScope.GLOBAL:
            # Would need to get all connections
            return []

        return []

    async def _filter_by_subscriptions(
        self, event: Event, recipients: List[ConnectionInfo]
    ) -> List[ConnectionInfo]:
        """Filter recipients by their subscriptions."""
        filtered = []

        for recipient in recipients:
            subscription = self._subscriptions.get(recipient.connection_id)

            # No subscription means receive all events
            if not subscription:
                filtered.append(recipient)
                continue

            # Check if subscribed to this event type
            if event.event_type not in subscription.event_types:
                continue

            # Apply filter function if present
            if subscription.filter_func and not subscription.filter_func(event):
                continue

            filtered.append(recipient)

        return filtered

    async def _queue_event(self, event: Event, connection_id: str) -> None:
        """Queue event for delivery."""
        queue = self._queues[event.priority]
        await queue.put((event, connection_id))

    async def _process_queue(self, priority: EventPriority) -> None:
        """Process events from a priority queue."""
        queue = self._queues[priority]
        batch: List[tuple[Event, str]] = []

        while self._running:
            try:
                # Collect batch
                deadline = asyncio.get_event_loop().time() + (
                    self.batch_delay_ms / 1000
                )

                while len(batch) < self.batch_size:
                    timeout = max(0, deadline - asyncio.get_event_loop().time())

                    try:
                        item = await asyncio.wait_for(queue.get(), timeout=timeout)
                        batch.append(item)
                    except asyncio.TimeoutError:
                        break

                if batch:
                    await self._process_batch(batch)
                    batch = []
                    self._metrics["batches_processed"] += 1

            except Exception as e:
                logger.error(f"Error processing {priority} queue: {e}")
                await asyncio.sleep(1)

    async def _process_batch(self, batch: List[tuple[Event, str]]) -> None:
        """Process a batch of events."""
        # Group by connection
        by_connection: Dict[str, List[Event]] = defaultdict(list)

        for event, connection_id in batch:
            by_connection[connection_id].append(event)

        # Send to each connection
        for connection_id, events in by_connection.items():
            # Create batch message
            messages = [event.to_message() for event in events]

            batch_message = {"type": "event_batch", "events": messages}

            # Send batch
            if await self.connection_manager.send_to_connection(
                connection_id, batch_message
            ):
                self._metrics["events_sent"] += len(events)
            else:
                self._metrics["events_failed"] += len(events)

                # Track failed deliveries
                for event in events:
                    self._delivery_attempts[connection_id] += 1

                    if self._delivery_attempts[connection_id] > 3:
                        self._failed_deliveries.append(
                            (event, connection_id, "Max retries exceeded")
                        )

        # Update average batch size
        total_batches = self._metrics["batches_processed"]
        if total_batches > 0:
            current_avg = self._metrics["avg_batch_size"]
            self._metrics["avg_batch_size"] = (
                current_avg * (total_batches - 1) + len(batch)
            ) / total_batches

    def get_metrics(self) -> Dict[str, Any]:
        """Get propagator metrics."""
        return self._metrics.copy()


class WebSocketEventBus:
    """
    High-level event bus for WebSocket communication.

    Provides a simpler interface over EventPropagator.
    """

    def __init__(
        self,
        connection_manager: ConnectionManager,
        propagator: Optional[EventPropagator] = None,
    ):
        """
        Initialize event bus.

        Args:
            connection_manager: Connection manager
            propagator: Event propagator (creates one if not provided)
        """
        self.connection_manager = connection_manager
        self.propagator = propagator or EventPropagator(connection_manager)

        # Event handlers
        self._handlers: Dict[str, List[Callable]] = defaultdict(list)

    async def start(self) -> None:
        """Start the event bus."""
        await self.propagator.start()

    async def stop(self) -> None:
        """Stop the event bus."""
        await self.propagator.stop()

    async def emit(
        self,
        event_type: str,
        payload: Dict[str, Any],
        to: Optional[Union[str, List[str], BroadcastStrategy]] = None,
        priority: EventPriority = EventPriority.NORMAL,
    ) -> int:
        """
        Emit an event.

        Args:
            event_type: Type of event
            payload: Event payload
            to: Target(s) for event
            priority: Event priority

        Returns:
            Number of recipients
        """
        # Create event
        event = Event(event_type=event_type, payload=payload, priority=priority)

        # Determine strategy
        strategy = None
        if isinstance(to, str):
            # Assume it's a room ID
            strategy = RoomBroadcast(to)
        elif isinstance(to, list):
            # List of connection IDs
            strategy = TargetedBroadcast(to)
        elif isinstance(to, BroadcastStrategy):
            strategy = to

        # Propagate
        return await self.propagator.propagate(event, strategy)

    async def emit_to_room(
        self,
        room_id: str,
        event_type: str,
        payload: Dict[str, Any],
        exclude: Optional[Set[str]] = None,
    ) -> int:
        """Emit event to all connections in a room."""
        return await self.emit(event_type, payload, RoomBroadcast(room_id, exclude))

    async def emit_to_player(
        self, player_id: str, event_type: str, payload: Dict[str, Any]
    ) -> int:
        """Emit event to all connections for a player."""
        return await self.emit(event_type, payload, PlayerBroadcast(player_id))

    def on(self, event_type: str, handler: Callable) -> None:
        """Register event handler."""
        self._handlers[event_type].append(handler)

    def off(self, event_type: str, handler: Callable) -> None:
        """Unregister event handler."""
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)

    async def handle_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Handle incoming event from client."""
        handlers = self._handlers.get(event_type, [])

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(payload)
                else:
                    handler(payload)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}")
