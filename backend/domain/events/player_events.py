# domain/events/player_events.py
"""
Domain events related to player actions and state changes.
"""

from dataclasses import dataclass
from typing import Optional
from .base import DomainEvent


@dataclass(frozen=True)
class PlayerJoinedEvent(DomainEvent):
    """Event raised when a player joins a room/game."""
    room_id: str
    player_name: str
    is_bot: bool
    slot_number: int


@dataclass(frozen=True)
class PlayerLeftEvent(DomainEvent):
    """Event raised when a player leaves a room/game."""
    room_id: str
    player_name: str
    reason: str  # "voluntary", "timeout", "kicked"


@dataclass(frozen=True)
class PlayerDisconnectedEvent(DomainEvent):
    """Event raised when a player disconnects (but doesn't leave)."""
    room_id: str
    player_name: str
    will_be_replaced_by_bot: bool


@dataclass(frozen=True)
class PlayerReconnectedEvent(DomainEvent):
    """Event raised when a player reconnects."""
    room_id: str
    player_name: str
    time_disconnected_seconds: float


@dataclass(frozen=True)
class PlayerReplacedByBotEvent(DomainEvent):
    """Event raised when a disconnected player is replaced by a bot."""
    room_id: str
    player_name: str
    bot_name: str
    reason: str  # "timeout", "game_started"


@dataclass(frozen=True)
class PlayerPromotedToHostEvent(DomainEvent):
    """Event raised when a player becomes the room host."""
    room_id: str
    player_name: str
    previous_host: Optional[str]
    reason: str  # "host_left", "host_disconnected"


@dataclass(frozen=True)
class PlayerStatisticsUpdatedEvent(DomainEvent):
    """Event raised when player statistics are updated."""
    player_name: str
    statistic_type: str  # "turns_won", "perfect_rounds", "games_won"
    old_value: int
    new_value: int
    game_id: Optional[str] = None