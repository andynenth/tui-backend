"""
DTOs for lobby use cases.

These DTOs define the request and response structures for
lobby operations like room discovery and listing.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid
from .base import Request, Response, PagedResponse
from .common import RoomInfo


# GetRoomList Use Case DTOs


@dataclass
class GetRoomListRequest(Request):
    """Request to get list of available rooms."""

    player_id: Optional[str] = None
    include_private: bool = False
    include_full: bool = False
    include_in_game: bool = False
    filter_by_host: Optional[str] = None
    sort_by: str = "created_at"  # created_at, player_count, room_name
    sort_order: str = "desc"  # asc, desc
    page: int = 1
    page_size: int = 20
    # Base request fields
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    correlation_id: Optional[str] = None


@dataclass
class RoomSummary:
    """Summary information about a room for listing."""

    room_id: str
    room_code: str
    room_name: str
    host_name: str
    player_count: int
    max_players: int
    game_in_progress: bool
    is_private: bool
    created_at: datetime

    @property
    def is_joinable(self) -> bool:
        """Check if room can be joined."""
        return self.player_count < self.max_players and not self.game_in_progress

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "room_id": self.room_id,
            "room_code": self.room_code,
            "room_name": self.room_name,
            "host_name": self.host_name,
            "player_count": self.player_count,
            "max_players": self.max_players,
            "game_in_progress": self.game_in_progress,
            "is_private": self.is_private,
            "is_joinable": self.is_joinable,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class GetRoomListResponse(PagedResponse):
    """Response with list of rooms."""

    rooms: List[RoomSummary] = field(default_factory=list)
    player_current_room: Optional[RoomSummary] = None

    def _get_data(self) -> Dict[str, Any]:
        """Include rooms and pagination in response data."""
        data = {
            "rooms": [room.to_dict() for room in self.rooms],
            "pagination": {
                "page": self.page,
                "page_size": self.page_size,
                "total_items": self.total_items,
                "total_pages": self.total_pages,
            },
        }

        if self.player_current_room:
            data["player_current_room"] = self.player_current_room.to_dict()

        return data


# GetRoomDetails Use Case DTOs


@dataclass
class GetRoomDetailsRequest(Request):
    """Request to get detailed information about a specific room."""

    room_code: Optional[str] = None
    room_id: Optional[str] = None
    requesting_player_id: Optional[str] = None
    include_game_details: bool = True
    include_player_stats: bool = True
    # Base request fields
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    correlation_id: Optional[str] = None


@dataclass
class RoomDetails:
    """Detailed information about a room."""

    room_info: RoomInfo
    game_settings: Dict[str, Any]
    game_state_summary: Optional[Dict[str, Any]] = None
    player_stats: Optional[Dict[str, Dict[str, Any]]] = None
    is_joinable: bool = True
    join_restrictions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = {
            "room": self.room_info.__dict__,
            "game_settings": self.game_settings,
            "is_joinable": self.is_joinable,
            "join_restrictions": self.join_restrictions,
        }

        if self.game_state_summary:
            data["game_state_summary"] = self.game_state_summary

        if self.player_stats:
            data["player_stats"] = self.player_stats

        return data


@dataclass
class GetRoomDetailsResponse(Response):
    """Response with detailed room information."""

    room_details: RoomDetails
    can_join: bool
    join_error: Optional[str] = None

    def _get_data(self) -> Dict[str, Any]:
        """Include room details in response data."""
        data = {"room_details": self.room_details.to_dict(), "can_join": self.can_join}

        if self.join_error:
            data["join_error"] = self.join_error

        return data
