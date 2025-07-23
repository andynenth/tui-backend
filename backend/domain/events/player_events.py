# domain/events/player_events.py
"""
Domain events related to player actions and state changes.
"""

from dataclasses import dataclass
from typing import Optional
from .base import SimpleDomainEvent


@dataclass(frozen=True, kw_only=True)
class RoomCreatedEvent(SimpleDomainEvent):
    """Event raised when a new room is created."""
    room_id: str
    host_name: str
    max_players: int = 4


@dataclass(frozen=True, kw_only=True)
class RoomClosedEvent(SimpleDomainEvent):
    """Event raised when a room is closed."""
    room_id: str
    reason: str  # "host_left", "game_completed", "manual_close", etc.
    closed_by: Optional[str] = None


@dataclass(frozen=True, kw_only=True)
class PlayerJoinedEvent(SimpleDomainEvent):
    """Event raised when a player joins a room/game."""
    room_id: str
    player_name: str
    is_bot: bool
    slot_number: int


@dataclass(frozen=True, kw_only=True)
class PlayerLeftEvent(SimpleDomainEvent):
    """Event raised when a player leaves a room/game."""
    room_id: str
    player_name: str
    reason: str  # "voluntary", "timeout", "kicked"


@dataclass(frozen=True, kw_only=True)
class PlayerDisconnectedEvent(SimpleDomainEvent):
    """Event raised when a player disconnects (but doesn't leave)."""
    room_id: str
    player_name: str
    will_be_replaced_by_bot: bool


@dataclass(frozen=True, kw_only=True)
class PlayerReconnectedEvent(SimpleDomainEvent):
    """Event raised when a player reconnects."""
    room_id: str
    player_name: str
    time_disconnected_seconds: float


@dataclass(frozen=True, kw_only=True)
class PlayerReplacedByBotEvent(SimpleDomainEvent):
    """Event raised when a disconnected player is replaced by a bot."""
    room_id: str
    player_name: str
    bot_name: str
    reason: str  # "timeout", "game_started"


@dataclass(frozen=True, kw_only=True)
class BotAddedEvent(SimpleDomainEvent):
    """Event raised when a bot is added to a room."""
    room_id: str
    bot_name: str
    difficulty: str
    slot_number: int


@dataclass(frozen=True, kw_only=True)
class BotRemovedEvent(SimpleDomainEvent):
    """Event raised when a bot is removed from a room."""
    room_id: str
    bot_name: str
    removed_by: str


@dataclass(frozen=True, kw_only=True)
class PlayerPromotedToHostEvent(SimpleDomainEvent):
    """Event raised when a player becomes the room host."""
    room_id: str
    player_name: str
    previous_host: Optional[str]
    reason: str  # "host_left", "host_disconnected"


@dataclass(frozen=True, kw_only=True)
class HostTransferredEvent(SimpleDomainEvent):
    """Event raised when host is transferred to another player."""
    room_id: str
    new_host: str
    previous_host: str
    reason: str  # "manual_transfer", "host_left", "host_disconnected"


@dataclass(frozen=True, kw_only=True)
class PlayerStatisticsUpdatedEvent(SimpleDomainEvent):
    """Event raised when player statistics are updated."""
    player_name: str
    statistic_type: str  # "turns_won", "perfect_rounds", "games_won"
    old_value: int
    new_value: int
    game_id: Optional[str] = None