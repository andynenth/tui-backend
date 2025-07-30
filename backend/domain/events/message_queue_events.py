"""
Message queue domain events.

These events track message queuing for disconnected players
and delivery of queued messages on reconnection.
"""

from dataclasses import dataclass
from typing import Dict, Any

from .base import GameEvent


@dataclass(frozen=True)
class MessageQueued(GameEvent):
    """Emitted when a message is queued for a disconnected player."""

    player_name: str
    event_type_queued: str
    is_critical: bool
    queue_size: int

    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update(
            {
                "player_name": self.player_name,
                "event_type_queued": self.event_type_queued,
                "is_critical": self.is_critical,
                "queue_size": self.queue_size,
            }
        )
        return data


@dataclass(frozen=True)
class QueuedMessagesDelivered(GameEvent):
    """Emitted when queued messages are delivered on reconnect."""

    player_name: str
    message_count: int
    oldest_message_age_seconds: float
    critical_message_count: int

    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update(
            {
                "player_name": self.player_name,
                "message_count": self.message_count,
                "oldest_message_age_seconds": self.oldest_message_age_seconds,
                "critical_message_count": self.critical_message_count,
            }
        )
        return data


@dataclass(frozen=True)
class MessageQueueOverflow(GameEvent):
    """Emitted when message queue reaches capacity and messages are dropped."""

    player_name: str
    dropped_count: int
    retained_critical_count: int
    queue_capacity: int

    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update(
            {
                "player_name": self.player_name,
                "dropped_count": self.dropped_count,
                "retained_critical_count": self.retained_critical_count,
                "queue_capacity": self.queue_capacity,
            }
        )
        return data
