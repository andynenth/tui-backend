"""
Game-specific message queue integration.

Provides specialized queuing for game events and tasks.
"""

from typing import Dict, Any, Optional, List, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import logging

from .base import Message, MessagePriority, MessageHandler, DeliveryOptions, T
from .memory_queue import PriorityInMemoryQueue
from .routing import TopicRouter
from .handlers import (
    AsyncMessageHandler,
    BatchMessageHandler,
    RetryingHandler,
    TimeoutHandler,
)
from .dead_letter import DeadLetterQueue, DeadLetterPolicy


logger = logging.getLogger(__name__)


class GameEventType(Enum):
    """Types of game events."""

    # Room events
    ROOM_CREATED = "room.created"
    ROOM_JOINED = "room.joined"
    ROOM_LEFT = "room.left"
    ROOM_CLOSED = "room.closed"

    # Game lifecycle
    GAME_STARTED = "game.started"
    GAME_ENDED = "game.ended"
    GAME_PAUSED = "game.paused"
    GAME_RESUMED = "game.resumed"

    # Game play
    TURN_STARTED = "turn.started"
    TURN_ENDED = "turn.ended"
    PIECE_PLAYED = "piece.played"
    DECLARATION_MADE = "declaration.made"
    REDEAL_REQUESTED = "redeal.requested"

    # Player events
    PLAYER_CONNECTED = "player.connected"
    PLAYER_DISCONNECTED = "player.disconnected"
    PLAYER_READY = "player.ready"
    PLAYER_ACTION = "player.action"

    # System events
    STATE_CHANGED = "state.changed"
    ERROR_OCCURRED = "error.occurred"
    METRIC_RECORDED = "metric.recorded"


@dataclass
class GameEvent:
    """
    Game event data structure.

    Contains all information about a game event.
    """

    event_type: GameEventType
    room_id: str
    game_id: Optional[str] = None
    player_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None

    def to_topic(self) -> str:
        """Convert to topic string for routing."""
        parts = [self.event_type.value]

        if self.room_id:
            parts.append(self.room_id)

        return ".".join(parts)


class GameEventQueue:
    """
    Specialized event queue for game events.

    Features:
    - Priority handling for critical events
    - Topic-based routing
    - Event persistence
    - Analytics support
    """

    def __init__(
        self,
        name: str = "game_events",
        max_size: int = 10000,
        enable_persistence: bool = True,
    ):
        """Initialize game event queue."""
        self.name = name
        self._queue = PriorityInMemoryQueue(name)
        self._router = TopicRouter(f"{name}_router")
        self._handlers: Dict[str, List[MessageHandler]] = {}
        self._dlq = DeadLetterQueue(
            f"{name}_dlq", DeadLetterPolicy(max_retries=3, ttl=timedelta(hours=24))
        )
        self._persistence_enabled = enable_persistence
        self._stats = {
            "events_published": 0,
            "events_processed": 0,
            "events_failed": 0,
            "by_type": {},
        }

        # Register default queues
        self._router.register_queue("critical", self._queue)
        self._router.register_queue("normal", self._queue)
        self._router.register_queue("analytics", self._queue)

    async def publish(
        self, event: GameEvent, priority: MessagePriority = MessagePriority.NORMAL
    ) -> str:
        """Publish game event."""
        # Create message
        message = Message(payload=event, priority=priority)

        # Set metadata
        message.metadata.source = "game_system"
        message.metadata.destination = event.to_topic()
        message.metadata.correlation_id = event.correlation_id
        message.metadata.headers = {
            "event_type": event.event_type.value,
            "room_id": event.room_id,
            "game_id": event.game_id,
            "player_id": event.player_id,
        }

        # Determine priority
        if event.event_type in (
            GameEventType.ERROR_OCCURRED,
            GameEventType.PLAYER_DISCONNECTED,
        ):
            message.priority = MessagePriority.CRITICAL
        elif event.event_type in (GameEventType.GAME_STARTED, GameEventType.GAME_ENDED):
            message.priority = MessagePriority.HIGH

        # Route to appropriate queues
        topic = event.to_topic()
        destinations = await self._router.route(message, topic)

        # Update stats
        self._stats["events_published"] += 1
        event_type = event.event_type.value
        self._stats["by_type"][event_type] = (
            self._stats["by_type"].get(event_type, 0) + 1
        )

        logger.debug(
            f"Published event {event.event_type.value} to {len(destinations)} queues"
        )

        return message.metadata.message_id

    def subscribe(
        self,
        pattern: str,
        handler: MessageHandler[GameEvent],
        queue_name: str = "normal",
    ) -> None:
        """Subscribe to game events matching pattern."""
        # Register route
        self._router.register_route(pattern, queue_name)

        # Store handler
        if pattern not in self._handlers:
            self._handlers[pattern] = []
        self._handlers[pattern].append(handler)

        logger.info(f"Subscribed to pattern '{pattern}' with handler {handler}")

    async def process_events(
        self, max_events: Optional[int] = None, timeout: Optional[float] = None
    ) -> int:
        """Process queued events."""
        processed = 0
        start_time = datetime.utcnow()

        while max_events is None or processed < max_events:
            # Check timeout
            if timeout:
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                if elapsed >= timeout:
                    break

            # Get next message
            message = await self._queue.dequeue(timeout=1.0)
            if not message:
                continue

            try:
                # Process event
                event = message.payload
                await self._process_event(event, message)

                # Acknowledge
                await self._queue.acknowledge(message.metadata.message_id)

                processed += 1
                self._stats["events_processed"] += 1

            except Exception as e:
                logger.error(f"Failed to process event: {e}")
                self._stats["events_failed"] += 1

                # Send to DLQ
                await self._dlq.add(
                    message,
                    reason=DeadLetterReason.PROCESSING_FAILED,
                    error=e,
                    original_queue=self.name,
                )

        return processed

    async def _process_event(
        self, event: GameEvent, message: Message[GameEvent]
    ) -> None:
        """Process individual event."""
        topic = event.to_topic()

        # Find matching handlers
        for pattern, handlers in self._handlers.items():
            if self._matches_pattern(topic, pattern):
                for handler in handlers:
                    if handler.can_handle(message):
                        await handler.handle(message)

    def _matches_pattern(self, topic: str, pattern: str) -> bool:
        """Check if topic matches pattern."""
        # Simple wildcard matching
        if pattern == "*":
            return True

        pattern_parts = pattern.split(".")
        topic_parts = topic.split(".")

        if len(pattern_parts) > len(topic_parts):
            return False

        for i, (pattern_part, topic_part) in enumerate(zip(pattern_parts, topic_parts)):
            if pattern_part == "*":
                continue
            elif pattern_part == "#":
                return True
            elif pattern_part != topic_part:
                return False

        return len(pattern_parts) == len(topic_parts)

    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        return {
            **self._stats,
            "queue_size": asyncio.create_task(self._queue.size()),
            "dlq_size": asyncio.create_task(self._dlq.size()),
        }


class GameEventHandler(MessageHandler[GameEvent]):
    """
    Base handler for game events.

    Provides common functionality for game event processing.
    """

    def __init__(
        self,
        event_types: Optional[Set[GameEventType]] = None,
        room_filter: Optional[str] = None,
        name: Optional[str] = None,
    ):
        """Initialize game event handler."""
        self.event_types = event_types
        self.room_filter = room_filter
        self.name = name or f"game_handler_{id(self)}"

    async def handle(self, message: Message[GameEvent]) -> None:
        """Handle game event."""
        event = message.payload

        # Validate event
        if not self._should_handle(event):
            return

        # Process event
        await self.process_event(event)

    async def process_event(self, event: GameEvent) -> None:
        """Process the game event. Override in subclasses."""
        raise NotImplementedError

    def can_handle(self, message: Message[GameEvent]) -> bool:
        """Check if can handle event."""
        return self._should_handle(message.payload)

    def _should_handle(self, event: GameEvent) -> bool:
        """Check if should handle event."""
        # Check event type
        if self.event_types and event.event_type not in self.event_types:
            return False

        # Check room filter
        if self.room_filter and event.room_id != self.room_filter:
            return False

        return True


class GameEventRouter:
    """
    Routes game events to appropriate handlers.

    Features:
    - Event type routing
    - Room-based routing
    - Handler registration
    """

    def __init__(self):
        """Initialize game event router."""
        self._handlers_by_type: Dict[GameEventType, List[GameEventHandler]] = {}
        self._handlers_by_room: Dict[str, List[GameEventHandler]] = {}
        self._global_handlers: List[GameEventHandler] = []

    def register_handler(
        self,
        handler: GameEventHandler,
        event_types: Optional[List[GameEventType]] = None,
        room_id: Optional[str] = None,
    ) -> None:
        """Register event handler."""
        if event_types:
            for event_type in event_types:
                if event_type not in self._handlers_by_type:
                    self._handlers_by_type[event_type] = []
                self._handlers_by_type[event_type].append(handler)

        if room_id:
            if room_id not in self._handlers_by_room:
                self._handlers_by_room[room_id] = []
            self._handlers_by_room[room_id].append(handler)

        if not event_types and not room_id:
            self._global_handlers.append(handler)

    async def route_event(self, event: GameEvent) -> None:
        """Route event to appropriate handlers."""
        handlers = set()

        # Get type-specific handlers
        if event.event_type in self._handlers_by_type:
            handlers.update(self._handlers_by_type[event.event_type])

        # Get room-specific handlers
        if event.room_id in self._handlers_by_room:
            handlers.update(self._handlers_by_room[event.room_id])

        # Add global handlers
        handlers.update(self._global_handlers)

        # Create message
        message = Message(payload=event)

        # Process with all handlers
        for handler in handlers:
            if handler.can_handle(message):
                try:
                    await handler.handle(message)
                except Exception as e:
                    logger.error(f"Handler {handler.name} failed: {e}")


class GameTaskProcessor:
    """
    Processes background game tasks.

    Features:
    - Bot move calculation
    - Game state archival
    - Analytics processing
    - Cleanup tasks
    """

    def __init__(
        self, task_queue: Optional[PriorityInMemoryQueue] = None, max_workers: int = 5
    ):
        """Initialize task processor."""
        self.task_queue = task_queue or PriorityInMemoryQueue("game_tasks")
        self.max_workers = max_workers
        self._workers: List[asyncio.Task] = []
        self._shutdown = False
        self._task_handlers: Dict[str, Callable] = {}

        # Register default handlers
        self._register_default_handlers()

    def register_task_handler(
        self, task_type: str, handler: Callable[[Dict[str, Any]], Any]
    ) -> None:
        """Register handler for task type."""
        self._task_handlers[task_type] = handler

    async def submit_task(
        self,
        task_type: str,
        data: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        delay: Optional[timedelta] = None,
    ) -> str:
        """Submit task for processing."""
        # Create task message
        task_data = {
            "type": task_type,
            "data": data,
            "submitted_at": datetime.utcnow().isoformat(),
        }

        message = Message(payload=task_data, priority=priority)

        # Set delivery options
        options = DeliveryOptions(priority=priority)
        if delay:
            options.delay = delay

        # Enqueue
        task_id = await self.task_queue.enqueue(message, options)

        logger.info(f"Submitted task {task_type} with ID {task_id}")

        return task_id

    async def start(self) -> None:
        """Start task processing workers."""
        self._shutdown = False

        # Start workers
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker_loop(i))
            self._workers.append(worker)

        logger.info(f"Started {self.max_workers} task workers")

    async def stop(self) -> None:
        """Stop task processing."""
        self._shutdown = True

        # Wait for workers
        if self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)

        self._workers.clear()
        logger.info("Task processor stopped")

    async def _worker_loop(self, worker_id: int) -> None:
        """Worker loop for processing tasks."""
        logger.info(f"Worker {worker_id} started")

        while not self._shutdown:
            try:
                # Get task
                message = await self.task_queue.dequeue(timeout=1.0)
                if not message:
                    continue

                # Process task
                task_data = message.payload
                task_type = task_data.get("type")

                handler = self._task_handlers.get(task_type)
                if handler:
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(task_data["data"])
                        else:
                            await asyncio.get_event_loop().run_in_executor(
                                None, handler, task_data["data"]
                            )

                        # Acknowledge
                        await self.task_queue.acknowledge(message.metadata.message_id)

                    except Exception as e:
                        logger.error(f"Task {task_type} failed: {e}")
                        await self.task_queue.reject(
                            message.metadata.message_id,
                            requeue=message.metadata.attempts < 3,
                        )
                else:
                    logger.warning(f"No handler for task type: {task_type}")
                    await self.task_queue.acknowledge(message.metadata.message_id)

            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")

        logger.info(f"Worker {worker_id} stopped")

    def _register_default_handlers(self) -> None:
        """Register default task handlers."""

        # Bot move calculation
        async def calculate_bot_move(data: Dict[str, Any]) -> None:
            game_id = data["game_id"]
            player_id = data["player_id"]
            logger.info(f"Calculating bot move for game {game_id}, player {player_id}")
            # Bot logic would go here

        self.register_task_handler("bot_move", calculate_bot_move)

        # Game archival
        async def archive_game(data: Dict[str, Any]) -> None:
            game_id = data["game_id"]
            logger.info(f"Archiving game {game_id}")
            # Archival logic would go here

        self.register_task_handler("archive_game", archive_game)

        # Cleanup
        async def cleanup_room(data: Dict[str, Any]) -> None:
            room_id = data["room_id"]
            logger.info(f"Cleaning up room {room_id}")
            # Cleanup logic would go here

        self.register_task_handler("cleanup_room", cleanup_room)
