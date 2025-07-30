"""
Lobby-related domain events.
"""

from dataclasses import dataclass
from typing import List, Dict, Any
from .base import DomainEvent


@dataclass(frozen=True)
class RoomListRequested(DomainEvent):
    """A client has requested the list of available rooms."""

    requested_by_id: str

    def _get_event_data(self) -> Dict[str, Any]:
        return {"requested_by_id": self.requested_by_id}


@dataclass(frozen=True)
class RoomListUpdated(DomainEvent):
    """The room list has been updated."""

    rooms: List[Dict[str, Any]]
    reason: str  # "room_created", "room_closed", "player_joined", etc.

    def _get_event_data(self) -> Dict[str, Any]:
        return {"rooms": self.rooms, "reason": self.reason}
