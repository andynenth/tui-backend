"""
DTOs for room management use cases.

These DTOs define the request and response structures for
room-related operations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid
from .base import Request, Response
from .common import PlayerInfo, RoomInfo


# CreateRoom Use Case DTOs

@dataclass
class CreateRoomRequest(Request):
    """Request to create a new room."""
    
    host_player_id: str
    host_player_name: str
    room_name: Optional[str] = None
    max_players: int = 4
    win_condition_type: str = "score"
    win_condition_value: int = 50
    allow_bots: bool = True
    is_private: bool = False
    # Base request fields
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    correlation_id: Optional[str] = None


@dataclass
class CreateRoomResponse:
    """Response from creating a room."""
    
    # Response-specific fields
    room_info: RoomInfo
    join_code: str
    
    # Base Response fields
    success: bool = True
    request_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary for serialization."""
        return {
            "success": self.success,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
            "data": self._get_data()
        }
    
    def _get_data(self) -> Dict[str, Any]:
        """Include room info in response data."""
        return {
            "room": self.room_info.__dict__,
            "join_code": self.join_code
        }


# JoinRoom Use Case DTOs

@dataclass
class JoinRoomRequest(Request):
    """Request to join a room."""
    
    player_id: str
    player_name: str
    room_code: Optional[str] = None
    room_id: Optional[str] = None
    seat_preference: Optional[int] = None
    # Base request fields
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    correlation_id: Optional[str] = None


@dataclass
class JoinRoomResponse(Response):
    """Response from joining a room."""
    
    room_info: RoomInfo
    seat_position: int
    is_host: bool
    # Base response fields
    success: bool = True
    request_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def _get_data(self) -> Dict[str, Any]:
        """Include join details in response data."""
        return {
            "room": self.room_info.__dict__,
            "seat_position": self.seat_position,
            "is_host": self.is_host
        }


# LeaveRoom Use Case DTOs

@dataclass
class LeaveRoomRequest(Request):
    """Request to leave a room."""
    
    player_id: str
    room_id: str
    reason: Optional[str] = None
    # Base request fields
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    correlation_id: Optional[str] = None


@dataclass
class LeaveRoomResponse(Response):
    """Response from leaving a room."""
    
    room_id: str
    new_host_id: Optional[str] = None
    room_closed: bool = False
    
    def _get_data(self) -> Dict[str, Any]:
        """Include leave details in response data."""
        return {
            "room_id": self.room_id,
            "new_host_id": self.new_host_id,
            "room_closed": self.room_closed
        }


# GetRoomState Use Case DTOs

@dataclass
class GetRoomStateRequest(Request):
    """Request to get current room state."""
    
    room_id: str
    requesting_player_id: Optional[str] = None
    include_game_state: bool = True
    # Base request fields
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    correlation_id: Optional[str] = None


@dataclass
class GetRoomStateResponse(Response):
    """Response with room state."""
    
    room_info: RoomInfo
    game_state: Optional[Dict[str, Any]] = None
    # Base response fields
    success: bool = True
    request_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def _get_data(self) -> Dict[str, Any]:
        """Include all state in response data."""
        data = {"room": self.room_info.__dict__}
        if self.game_state:
            data["game_state"] = self.game_state
        return data


# AddBot Use Case DTOs

@dataclass
class AddBotRequest(Request):
    """Request to add a bot to a room."""
    
    room_id: str
    requesting_player_id: str
    bot_difficulty: str = "medium"
    bot_name: Optional[str] = None
    seat_position: Optional[int] = None
    # Base request fields
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    correlation_id: Optional[str] = None


@dataclass
class AddBotResponse(Response):
    """Response from adding a bot."""
    
    bot_info: PlayerInfo
    room_info: RoomInfo
    
    def _get_data(self) -> Dict[str, Any]:
        """Include bot and room info in response data."""
        return {
            "bot": self.bot_info.__dict__,
            "room": self.room_info.__dict__
        }


# RemovePlayer Use Case DTOs

@dataclass
class RemovePlayerRequest(Request):
    """Request to remove a player from a room."""
    
    room_id: str
    requesting_player_id: str
    target_player_id: str
    reason: Optional[str] = None
    # Base request fields
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    correlation_id: Optional[str] = None


@dataclass
class RemovePlayerResponse(Response):
    """Response from removing a player."""
    
    removed_player_id: str
    room_info: RoomInfo
    was_bot: bool = False
    
    def _get_data(self) -> Dict[str, Any]:
        """Include removal details in response data."""
        return {
            "removed_player_id": self.removed_player_id,
            "room": self.room_info.__dict__,
            "was_bot": self.was_bot
        }