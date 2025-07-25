"""
Room management domain events.

These events represent changes to game rooms and player membership.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from .base import GameEvent


@dataclass(frozen=True)
class RoomCreated(GameEvent):
    """A new game room has been created."""
    host_id: str
    host_name: str
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'host_id': self.host_id,
            'host_name': self.host_name
        })
        return data


@dataclass(frozen=True)
class PlayerJoinedRoom(GameEvent):
    """A player has joined a game room."""
    player_id: str
    player_name: str
    player_slot: str  # P1, P2, P3, or P4
    is_bot: bool = False
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'player_id': self.player_id,
            'player_name': self.player_name,
            'player_slot': self.player_slot,
            'is_bot': self.is_bot
        })
        return data


@dataclass(frozen=True)
class PlayerLeftRoom(GameEvent):
    """A player has left a game room."""
    player_id: str
    player_name: str
    player_slot: str
    reason: Optional[str] = None
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'player_id': self.player_id,
            'player_name': self.player_name,
            'player_slot': self.player_slot,
            'reason': self.reason
        })
        return data


@dataclass(frozen=True)
class RoomClosed(GameEvent):
    """A game room has been closed."""
    reason: str
    final_player_count: int
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'reason': self.reason,
            'final_player_count': self.final_player_count
        })
        return data


@dataclass(frozen=True)
class HostChanged(GameEvent):
    """The host of a room has changed."""
    old_host_id: str
    old_host_name: str
    new_host_id: str
    new_host_name: str
    reason: str  # e.g., "host_left", "host_disconnected"
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'old_host_id': self.old_host_id,
            'old_host_name': self.old_host_name,
            'new_host_id': self.new_host_id,
            'new_host_name': self.new_host_name,
            'reason': self.reason
        })
        return data


@dataclass(frozen=True)
class BotAdded(GameEvent):
    """A bot has been added to a room."""
    bot_id: str
    bot_name: str
    player_slot: str
    added_by_id: str
    added_by_name: str
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'bot_id': self.bot_id,
            'bot_name': self.bot_name,
            'player_slot': self.player_slot,
            'added_by_id': self.added_by_id,
            'added_by_name': self.added_by_name
        })
        return data


@dataclass(frozen=True)
class PlayerRemoved(GameEvent):
    """A player has been removed from a room by the host."""
    removed_player_id: str
    removed_player_name: str
    removed_player_slot: str
    removed_by_id: str
    removed_by_name: str
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'removed_player_id': self.removed_player_id,
            'removed_player_name': self.removed_player_name,
            'removed_player_slot': self.removed_player_slot,
            'removed_by_id': self.removed_by_id,
            'removed_by_name': self.removed_by_name
        })
        return data


@dataclass(frozen=True)
class RoomStateRequested(GameEvent):
    """A player has requested the current room state."""
    requested_by_id: str
    requested_by_name: str
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'requested_by_id': self.requested_by_id,
            'requested_by_name': self.requested_by_name
        })
        return data