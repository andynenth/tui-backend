"""
State machine event stream for debugging and monitoring.

Provides real-time event streaming for state transitions,
actions, and system events.
"""

import asyncio
from typing import Dict, Any, Optional, List, Callable, Set
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
from collections import deque
import uuid


class EventType(Enum):
    """Types of events in the system."""
    # State machine events
    STATE_TRANSITION_START = "state.transition.start"
    STATE_TRANSITION_COMPLETE = "state.transition.complete"
    STATE_TRANSITION_FAILED = "state.transition.failed"
    
    # Action events
    ACTION_QUEUED = "action.queued"
    ACTION_PROCESSING = "action.processing"
    ACTION_COMPLETED = "action.completed"
    ACTION_FAILED = "action.failed"
    
    # Phase events
    PHASE_STARTED = "phase.started"
    PHASE_COMPLETED = "phase.completed"
    PHASE_TIMEOUT = "phase.timeout"
    
    # Game events
    GAME_CREATED = "game.created"
    GAME_STARTED = "game.started"
    GAME_ENDED = "game.ended"
    GAME_ERROR = "game.error"
    
    # Player events
    PLAYER_JOINED = "player.joined"
    PLAYER_LEFT = "player.left"
    PLAYER_ACTION = "player.action"
    PLAYER_TIMEOUT = "player.timeout"
    
    # System events
    BROADCAST_SENT = "broadcast.sent"
    BROADCAST_FAILED = "broadcast.failed"
    CONNECTION_OPENED = "connection.opened"
    CONNECTION_CLOSED = "connection.closed"
    ERROR_OCCURRED = "error.occurred"


@dataclass
class SystemEvent:
    """Represents a system event."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.STATE_TRANSITION_START
    timestamp: datetime = field(default_factory=datetime.utcnow)
    game_id: Optional[str] = None
    room_id: Optional[str] = None
    player_id: Optional[str] = None
    correlation_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.isoformat(),
            'game_id': self.game_id,
            'room_id': self.room_id,
            'player_id': self.player_id,
            'correlation_id': self.correlation_id,
            'data': self.data,
            'metadata': self.metadata
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class EventFilter:
    """Filter for event stream subscriptions."""
    
    def __init__(
        self,
        event_types: Optional[Set[EventType]] = None,
        game_ids: Optional[Set[str]] = None,
        room_ids: Optional[Set[str]] = None,
        player_ids: Optional[Set[str]] = None,
        correlation_ids: Optional[Set[str]] = None
    ):
        """Initialize event filter."""
        self.event_types = event_types
        self.game_ids = game_ids
        self.room_ids = room_ids
        self.player_ids = player_ids
        self.correlation_ids = correlation_ids
    
    def matches(self, event: SystemEvent) -> bool:
        """Check if event matches filter."""
        # Check event type
        if self.event_types and event.event_type not in self.event_types:
            return False
        
        # Check game ID
        if self.game_ids and event.game_id not in self.game_ids:
            return False
        
        # Check room ID
        if self.room_ids and event.room_id not in self.room_ids:
            return False
        
        # Check player ID
        if self.player_ids and event.player_id not in self.player_ids:
            return False
        
        # Check correlation ID
        if self.correlation_ids and event.correlation_id not in self.correlation_ids:
            return False
        
        return True


class EventSubscriber:
    """Subscriber for event stream."""
    
    def __init__(
        self,
        subscriber_id: str,
        filter: Optional[EventFilter] = None,
        queue_size: int = 1000
    ):
        """Initialize event subscriber."""
        self.subscriber_id = subscriber_id
        self.filter = filter or EventFilter()
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=queue_size)
        self.active = True
        self.created_at = datetime.utcnow()
        self.last_event_at: Optional[datetime] = None
        self.event_count = 0
    
    async def send_event(self, event: SystemEvent) -> bool:
        """Send event to subscriber if it matches filter."""
        if not self.active:
            return False
        
        if not self.filter.matches(event):
            return False
        
        try:
            await self.queue.put(event)
            self.last_event_at = datetime.utcnow()
            self.event_count += 1
            return True
        except asyncio.QueueFull:
            # Drop event if queue is full
            return False
    
    async def get_event(self, timeout: Optional[float] = None) -> Optional[SystemEvent]:
        """Get next event from queue."""
        if not self.active:
            return None
        
        try:
            if timeout:
                return await asyncio.wait_for(self.queue.get(), timeout)
            else:
                return await self.queue.get()
        except asyncio.TimeoutError:
            return None
    
    def close(self) -> None:
        """Close subscriber."""
        self.active = False


class EventStream:
    """
    Central event stream for debugging and monitoring.
    
    Features:
    - Real-time event streaming
    - Filtered subscriptions
    - Event history
    - Performance monitoring
    """
    
    def __init__(
        self,
        history_size: int = 10000,
        max_subscribers: int = 100
    ):
        """Initialize event stream."""
        self.history_size = history_size
        self.max_subscribers = max_subscribers
        
        # Event storage
        self._event_history: deque = deque(maxlen=history_size)
        self._subscribers: Dict[str, EventSubscriber] = {}
        
        # Statistics
        self._total_events = 0
        self._events_by_type: Dict[EventType, int] = {}
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
    
    async def publish_event(self, event: SystemEvent) -> None:
        """Publish event to stream."""
        async with self._lock:
            # Add to history
            self._event_history.append(event)
            
            # Update statistics
            self._total_events += 1
            self._events_by_type[event.event_type] = \
                self._events_by_type.get(event.event_type, 0) + 1
            
            # Send to subscribers
            tasks = []
            for subscriber in self._subscribers.values():
                task = asyncio.create_task(subscriber.send_event(event))
                tasks.append(task)
            
            # Wait for all sends to complete
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    async def subscribe(
        self,
        subscriber_id: Optional[str] = None,
        filter: Optional[EventFilter] = None
    ) -> EventSubscriber:
        """Subscribe to event stream."""
        if subscriber_id is None:
            subscriber_id = str(uuid.uuid4())
        
        async with self._lock:
            if len(self._subscribers) >= self.max_subscribers:
                raise RuntimeError(f"Maximum subscribers ({self.max_subscribers}) reached")
            
            if subscriber_id in self._subscribers:
                raise ValueError(f"Subscriber {subscriber_id} already exists")
            
            subscriber = EventSubscriber(subscriber_id, filter)
            self._subscribers[subscriber_id] = subscriber
            
            return subscriber
    
    async def unsubscribe(self, subscriber_id: str) -> None:
        """Unsubscribe from event stream."""
        async with self._lock:
            subscriber = self._subscribers.pop(subscriber_id, None)
            if subscriber:
                subscriber.close()
    
    def get_history(
        self,
        limit: Optional[int] = None,
        filter: Optional[EventFilter] = None
    ) -> List[SystemEvent]:
        """Get event history."""
        events = list(self._event_history)
        
        # Apply filter
        if filter:
            events = [e for e in events if filter.matches(e)]
        
        # Apply limit
        if limit:
            events = events[-limit:]
        
        return events
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get event stream statistics."""
        return {
            'total_events': self._total_events,
            'history_size': len(self._event_history),
            'subscriber_count': len(self._subscribers),
            'events_by_type': {
                event_type.value: count
                for event_type, count in self._events_by_type.items()
            },
            'subscribers': [
                {
                    'id': sub.subscriber_id,
                    'active': sub.active,
                    'event_count': sub.event_count,
                    'created_at': sub.created_at.isoformat(),
                    'last_event_at': sub.last_event_at.isoformat() if sub.last_event_at else None
                }
                for sub in self._subscribers.values()
            ]
        }
    
    async def cleanup_inactive_subscribers(
        self,
        inactive_timeout_minutes: int = 30
    ) -> int:
        """Clean up inactive subscribers."""
        from datetime import timedelta
        
        cutoff = datetime.utcnow() - timedelta(minutes=inactive_timeout_minutes)
        inactive_ids = []
        
        async with self._lock:
            for sub_id, subscriber in self._subscribers.items():
                last_active = subscriber.last_event_at or subscriber.created_at
                if last_active < cutoff:
                    inactive_ids.append(sub_id)
            
            for sub_id in inactive_ids:
                subscriber = self._subscribers.pop(sub_id)
                subscriber.close()
        
        return len(inactive_ids)


class EventLogger:
    """
    Helper class for logging events to the stream.
    """
    
    def __init__(self, event_stream: EventStream, default_metadata: Optional[Dict[str, Any]] = None):
        """Initialize event logger."""
        self.event_stream = event_stream
        self.default_metadata = default_metadata or {}
    
    async def log_state_transition(
        self,
        game_id: str,
        from_state: str,
        to_state: str,
        success: bool = True,
        error: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> None:
        """Log state transition event."""
        event_type = (
            EventType.STATE_TRANSITION_COMPLETE if success
            else EventType.STATE_TRANSITION_FAILED
        )
        
        event = SystemEvent(
            event_type=event_type,
            game_id=game_id,
            correlation_id=correlation_id,
            data={
                'from_state': from_state,
                'to_state': to_state,
                'success': success,
                'error': error
            },
            metadata=self.default_metadata
        )
        
        await self.event_stream.publish_event(event)
    
    async def log_action(
        self,
        game_id: str,
        action_type: str,
        player_id: str,
        status: str,  # 'queued', 'processing', 'completed', 'failed'
        data: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ) -> None:
        """Log action event."""
        event_type_map = {
            'queued': EventType.ACTION_QUEUED,
            'processing': EventType.ACTION_PROCESSING,
            'completed': EventType.ACTION_COMPLETED,
            'failed': EventType.ACTION_FAILED
        }
        
        event = SystemEvent(
            event_type=event_type_map.get(status, EventType.ACTION_QUEUED),
            game_id=game_id,
            player_id=player_id,
            correlation_id=correlation_id,
            data={
                'action_type': action_type,
                'status': status,
                **(data or {})
            },
            metadata=self.default_metadata
        )
        
        await self.event_stream.publish_event(event)
    
    async def log_error(
        self,
        error_type: str,
        error_message: str,
        game_id: Optional[str] = None,
        player_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        stack_trace: Optional[str] = None
    ) -> None:
        """Log error event."""
        event = SystemEvent(
            event_type=EventType.ERROR_OCCURRED,
            game_id=game_id,
            player_id=player_id,
            correlation_id=correlation_id,
            data={
                'error_type': error_type,
                'error_message': error_message,
                'stack_trace': stack_trace
            },
            metadata=self.default_metadata
        )
        
        await self.event_stream.publish_event(event)


# Global event stream instance
_global_event_stream: Optional[EventStream] = None


def get_event_stream() -> EventStream:
    """Get global event stream instance."""
    global _global_event_stream
    if _global_event_stream is None:
        _global_event_stream = EventStream()
    return _global_event_stream


def configure_event_stream(
    history_size: int = 10000,
    max_subscribers: int = 100
) -> EventStream:
    """Configure global event stream."""
    global _global_event_stream
    _global_event_stream = EventStream(history_size, max_subscribers)
    return _global_event_stream