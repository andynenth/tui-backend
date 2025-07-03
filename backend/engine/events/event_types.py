# backend/engine/events/event_types.py

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union
from enum import Enum, IntEnum
from datetime import datetime
import uuid


class EventType(str, Enum):
    """
    🎯 **Game Event Types** - Strongly-typed event definitions
    
    Defines all possible events in the game system for type-safe event handling.
    """
    
    # === Phase Management Events ===
    PHASE_CHANGE_REQUESTED = "phase_change_requested"
    PHASE_CHANGE_STARTED = "phase_change_started"
    PHASE_CHANGE_COMPLETED = "phase_change_completed"
    PHASE_CHANGE_FAILED = "phase_change_failed"
    
    # === Action Events ===
    ACTION_RECEIVED = "action_received"
    ACTION_VALIDATED = "action_validated"
    ACTION_EXECUTED = "action_executed"
    ACTION_REJECTED = "action_rejected"
    ACTION_FAILED = "action_failed"
    
    # === Game State Events ===
    STATE_UPDATED = "state_updated"
    STATE_SAVED = "state_saved"
    STATE_LOADED = "state_loaded"
    STATE_CORRUPTED = "state_corrupted"
    
    # === Broadcasting Events ===
    BROADCAST_REQUESTED = "broadcast_requested"
    BROADCAST_SENT = "broadcast_sent"
    BROADCAST_FAILED = "broadcast_failed"
    
    # === Bot Management Events ===
    BOT_NOTIFICATION_SENT = "bot_notification_sent"
    BOT_ACTION_REQUEST = "bot_action_request"
    BOT_RESPONSE_RECEIVED = "bot_response_received"
    
    # === Game Flow Events ===
    GAME_STARTED = "game_started"
    GAME_ENDED = "game_ended"
    ROUND_STARTED = "round_started"
    ROUND_ENDED = "round_ended"
    TURN_STARTED = "turn_started"
    TURN_ENDED = "turn_ended"
    
    # === Error Events ===
    ERROR_OCCURRED = "error_occurred"
    WARNING_ISSUED = "warning_issued"
    RECOVERY_ATTEMPTED = "recovery_attempted"
    
    # === System Events ===
    SYSTEM_INITIALIZED = "system_initialized"
    SYSTEM_SHUTDOWN = "system_shutdown"
    HEALTH_CHECK = "health_check"
    METRICS_COLLECTED = "metrics_collected"


class EventPriority(IntEnum):
    """
    Event priority levels for processing order.
    
    Higher numbers = higher priority, processed first.
    """
    LOW = 1
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20
    EMERGENCY = 99


@dataclass
class GameEvent(ABC):
    """
    🎯 **Base Game Event** - Abstract base for all game events
    
    Provides common event infrastructure with type safety and metadata.
    """
    
    # Event identification
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = field(init=False)
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Event processing
    priority: EventPriority = EventPriority.NORMAL
    room_id: Optional[str] = None
    player_id: Optional[str] = None
    
    # Event data
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Event flow control
    is_processed: bool = False
    is_cancelled: bool = False
    processing_errors: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Set event type based on class."""
        if not hasattr(self, 'event_type') or self.event_type is None:
            # Use class name to infer event type if not set
            class_name = self.__class__.__name__
            if class_name.endswith('Event'):
                # Convert CamelCase to snake_case
                import re
                snake_case = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', class_name[:-5])
                snake_case = re.sub('([a-z0-9])([A-Z])', r'\1_\2', snake_case).lower()
                try:
                    self.event_type = EventType(snake_case)
                except ValueError:
                    # Fallback to generic event type
                    self.event_type = EventType.STATE_UPDATED
    
    @abstractmethod
    def get_event_data(self) -> Dict[str, Any]:
        """Get event-specific data for processing."""
        pass
    
    def mark_processed(self):
        """Mark event as processed."""
        self.is_processed = True
    
    def cancel(self, reason: str = ""):
        """Cancel event processing."""
        self.is_cancelled = True
        if reason:
            self.metadata['cancellation_reason'] = reason
    
    def add_error(self, error: str):
        """Add processing error to event."""
        self.processing_errors.append(error)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.isoformat(),
            'priority': self.priority.value,
            'room_id': self.room_id,
            'player_id': self.player_id,
            'data': self.get_event_data(),
            'metadata': self.metadata,
            'is_processed': self.is_processed,
            'is_cancelled': self.is_cancelled,
            'processing_errors': self.processing_errors
        }


@dataclass
class PhaseChangeEvent(GameEvent):
    """
    🎯 **Phase Change Event** - Phase transition notifications
    
    Triggered when game phases change (preparation → declaration → turn → scoring).
    """
    
    old_phase: Optional[str] = None
    new_phase: str = ""
    reason: str = ""
    validation_result: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = EventType.PHASE_CHANGE_COMPLETED
    
    def get_event_data(self) -> Dict[str, Any]:
        return {
            'old_phase': self.old_phase,
            'new_phase': self.new_phase,
            'reason': self.reason,
            'validation_result': self.validation_result,
            **self.data
        }


@dataclass
class ActionEvent(GameEvent):
    """
    🎯 **Action Event** - Player/system action notifications
    
    Triggered when actions are received, validated, executed, or rejected.
    """
    
    action_type: str = ""
    player_name: str = ""
    action_payload: Dict[str, Any] = field(default_factory=dict)
    validation_result: Dict[str, Any] = field(default_factory=dict)
    execution_result: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = EventType.ACTION_RECEIVED
    
    def get_event_data(self) -> Dict[str, Any]:
        return {
            'action_type': self.action_type,
            'player_name': self.player_name,
            'action_payload': self.action_payload,
            'validation_result': self.validation_result,
            'execution_result': self.execution_result,
            **self.data
        }


@dataclass
class BroadcastEvent(GameEvent):
    """
    🎯 **Broadcast Event** - WebSocket communication notifications
    
    Triggered when messages are broadcast to clients.
    """
    
    broadcast_type: str = ""
    target_room: Optional[str] = None
    target_player: Optional[str] = None
    message_data: Dict[str, Any] = field(default_factory=dict)
    broadcast_result: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = EventType.BROADCAST_REQUESTED
    
    def get_event_data(self) -> Dict[str, Any]:
        return {
            'broadcast_type': self.broadcast_type,
            'target_room': self.target_room,
            'target_player': self.target_player,
            'message_data': self.message_data,
            'broadcast_result': self.broadcast_result,
            **self.data
        }


@dataclass
class BotNotificationEvent(GameEvent):
    """
    🎯 **Bot Notification Event** - Bot AI communication
    
    Triggered when bots need to be notified of game state changes.
    """
    
    notification_type: str = ""
    bot_targets: List[str] = field(default_factory=list)
    notification_data: Dict[str, Any] = field(default_factory=dict)
    notification_result: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = EventType.BOT_NOTIFICATION_SENT
    
    def get_event_data(self) -> Dict[str, Any]:
        return {
            'notification_type': self.notification_type,
            'bot_targets': self.bot_targets,
            'notification_data': self.notification_data,
            'notification_result': self.notification_result,
            **self.data
        }


@dataclass
class StateUpdateEvent(GameEvent):
    """
    🎯 **State Update Event** - Game state change notifications
    
    Triggered when game state is updated, saved, or loaded.
    """
    
    state_type: str = ""  # e.g., "game_state", "player_state", "phase_data"
    state_data: Dict[str, Any] = field(default_factory=dict)
    previous_state: Optional[Dict[str, Any]] = None
    update_reason: str = ""
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = EventType.STATE_UPDATED
    
    def get_event_data(self) -> Dict[str, Any]:
        return {
            'state_type': self.state_type,
            'state_data': self.state_data,
            'previous_state': self.previous_state,
            'update_reason': self.update_reason,
            **self.data
        }


@dataclass
class ErrorEvent(GameEvent):
    """
    🎯 **Error Event** - Error and warning notifications
    
    Triggered when errors occur in the system.
    """
    
    error_type: str = ""
    error_message: str = ""
    error_details: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    recovery_suggestions: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = EventType.ERROR_OCCURRED
        self.priority = EventPriority.HIGH  # Errors are high priority
    
    def get_event_data(self) -> Dict[str, Any]:
        return {
            'error_type': self.error_type,
            'error_message': self.error_message,
            'error_details': self.error_details,
            'stack_trace': self.stack_trace,
            'recovery_suggestions': self.recovery_suggestions,
            **self.data
        }


# Event type mapping for factory creation
EVENT_TYPE_MAP = {
    EventType.PHASE_CHANGE_COMPLETED: PhaseChangeEvent,
    EventType.PHASE_CHANGE_REQUESTED: PhaseChangeEvent,
    EventType.PHASE_CHANGE_STARTED: PhaseChangeEvent,
    EventType.PHASE_CHANGE_FAILED: PhaseChangeEvent,
    
    EventType.ACTION_RECEIVED: ActionEvent,
    EventType.ACTION_VALIDATED: ActionEvent,
    EventType.ACTION_EXECUTED: ActionEvent,
    EventType.ACTION_REJECTED: ActionEvent,
    EventType.ACTION_FAILED: ActionEvent,
    
    EventType.BROADCAST_REQUESTED: BroadcastEvent,
    EventType.BROADCAST_SENT: BroadcastEvent,
    EventType.BROADCAST_FAILED: BroadcastEvent,
    
    EventType.BOT_NOTIFICATION_SENT: BotNotificationEvent,
    EventType.BOT_ACTION_REQUEST: BotNotificationEvent,
    EventType.BOT_RESPONSE_RECEIVED: BotNotificationEvent,
    
    EventType.STATE_UPDATED: StateUpdateEvent,
    EventType.STATE_SAVED: StateUpdateEvent,
    EventType.STATE_LOADED: StateUpdateEvent,
    EventType.STATE_CORRUPTED: StateUpdateEvent,
    
    EventType.ERROR_OCCURRED: ErrorEvent,
    EventType.WARNING_ISSUED: ErrorEvent,
}


def create_event(event_type: EventType, **kwargs) -> GameEvent:
    """
    Factory function to create strongly-typed events.
    
    Args:
        event_type: The type of event to create
        **kwargs: Event-specific data
    
    Returns:
        Strongly-typed event instance
    """
    event_class = EVENT_TYPE_MAP.get(event_type, StateUpdateEvent)
    return event_class(event_type=event_type, **kwargs)