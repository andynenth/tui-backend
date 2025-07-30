"""
Domain events - Immutable records of things that have happened.

Events are a key part of the domain model, representing facts about
state changes and important occurrences in the business domain.
"""

from .base import DomainEvent, GameEvent, EventMetadata
from .game_events import GameStarted, GameEnded
from .player_events import PlayerHandUpdated, PlayerDeclaredPiles
from .connection_events import (
    PlayerDisconnected,
    PlayerReconnected,
    BotActivated,
    BotDeactivated,
)
from .message_queue_events import (
    MessageQueued,
    QueuedMessagesDelivered,
    MessageQueueOverflow,
)

__all__ = [
    # Base
    "DomainEvent",
    "GameEvent",
    "EventMetadata",
    # Game events
    "GameStarted",
    "GameEnded",
    # Player events
    "PlayerHandUpdated",
    "PlayerDeclaredPiles",
    # Connection events
    "PlayerDisconnected",
    "PlayerReconnected",
    "BotActivated",
    "BotDeactivated",
    # Message queue events
    "MessageQueued",
    "QueuedMessagesDelivered",
    "MessageQueueOverflow",
]
