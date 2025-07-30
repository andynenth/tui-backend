"""
DTOs for connection management use cases.

These DTOs define the request and response structures for
connection-related operations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid
from .base import Request, Response
from .common import BaseRequest, BaseResponse


# HandlePing Use Case DTOs


@dataclass
class HandlePingRequest:
    """Request to handle a ping message."""

    # Required fields first
    player_id: str

    # Optional fields with defaults
    room_id: Optional[str] = None
    sequence_number: Optional[int] = None

    # Base Request fields
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    correlation_id: Optional[str] = None


@dataclass
class HandlePingResponse:
    """Response from handling a ping."""

    # Response-specific fields
    sequence_number: Optional[int] = None
    server_time: datetime = field(default_factory=datetime.utcnow)

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
            "data": self._get_data(),
        }

    def _get_data(self) -> Dict[str, Any]:
        """Get response-specific data."""
        return {
            "sequence_number": self.sequence_number,
            "server_time": self.server_time.isoformat(),
        }


# MarkClientReady Use Case DTOs


@dataclass
class MarkClientReadyRequest:
    """Request to mark a client as ready."""

    # Required fields first
    player_id: str
    room_id: str

    # Optional fields
    client_version: Optional[str] = None
    client_capabilities: Optional[Dict[str, Any]] = None

    # Base Request fields
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    correlation_id: Optional[str] = None


@dataclass
class MarkClientReadyResponse:
    """Response from marking client ready."""

    # Required fields first
    player_id: str
    is_ready: bool

    # Optional fields with defaults
    room_state_provided: bool = False

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
            "data": self._get_data(),
        }

    def _get_data(self) -> Dict[str, Any]:
        """Get response-specific data."""
        return {
            "player_id": self.player_id,
            "is_ready": self.is_ready,
            "room_state_provided": self.room_state_provided,
        }


# AcknowledgeMessage Use Case DTOs


@dataclass
class AcknowledgeMessageRequest:
    """Request to acknowledge a message."""

    # Required fields first
    player_id: str
    message_id: str
    message_type: str

    # Optional fields with defaults
    room_id: Optional[str] = None
    success: bool = True
    error_code: Optional[str] = None

    # Base Request fields
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    correlation_id: Optional[str] = None


@dataclass
class AcknowledgeMessageResponse:
    """Response from acknowledging a message."""

    # Required fields first
    message_id: str
    acknowledged: bool

    # Optional fields with defaults
    retry_required: bool = False

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
            "data": self._get_data(),
        }

    def _get_data(self) -> Dict[str, Any]:
        """Get response-specific data."""
        return {
            "message_id": self.message_id,
            "acknowledged": self.acknowledged,
            "retry_required": self.retry_required,
        }


# SyncClientState Use Case DTOs


@dataclass
class SyncClientStateRequest:
    """Request to synchronize client state."""

    # Required fields first
    player_id: str

    # Optional fields with defaults
    room_id: Optional[str] = None
    last_known_sequence: Optional[int] = None
    include_game_state: bool = True
    include_player_hands: bool = True

    # Base Request fields
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    correlation_id: Optional[str] = None


@dataclass
class SyncClientStateResponse:
    """Response with synchronized state."""

    # Required fields first
    player_id: str

    # Optional fields with defaults
    room_state: Optional[Dict[str, Any]] = None
    game_state: Optional[Dict[str, Any]] = None
    player_hand: Optional[Dict[str, Any]] = None
    current_sequence: int = 0
    events_missed: int = 0

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
            "data": self._get_data(),
        }

    def _get_data(self) -> Dict[str, Any]:
        """Include all state data in response."""
        return {
            "player_id": self.player_id,
            "room_state": self.room_state,
            "game_state": self.game_state,
            "player_hand": self.player_hand,
            "current_sequence": self.current_sequence,
            "events_missed": self.events_missed,
        }


# Disconnect/Reconnect DTOs


@dataclass
class HandlePlayerDisconnectRequest(BaseRequest):
    """Request to handle player disconnection."""

    room_id: str
    player_name: str
    activate_bot: bool = True


@dataclass
class HandlePlayerDisconnectResponse(BaseResponse):
    """Response from handling player disconnection."""

    bot_activated: bool = False
    queue_created: bool = False
    host_migrated: bool = False
    new_host_name: Optional[str] = None


@dataclass
class HandlePlayerReconnectRequest(BaseRequest):
    """Request to handle player reconnection."""

    room_id: str
    player_name: str
    websocket_id: str
    user_id: Optional[str] = None


@dataclass
class HandlePlayerReconnectResponse(BaseResponse):
    """Response from handling player reconnection."""

    bot_deactivated: bool = False
    messages_restored: int = 0
    queued_messages: List[Dict[str, Any]] = None
    current_state: Optional[Dict[str, Any]] = None
    room_cleanup_cancelled: bool = False

    def __post_init__(self):
        if self.queued_messages is None:
            self.queued_messages = []


@dataclass
class QueueMessageRequest(BaseRequest):
    """Request to queue a message for a player."""

    room_id: str
    player_name: str
    event_type: str
    event_data: Dict[str, Any]
    is_critical: bool = False


@dataclass
class QueueMessageResponse(BaseResponse):
    """Response from queuing a message."""

    queued: bool = False
    queue_size: int = 0
    message_dropped: bool = False
