"""
Connection entity - Tracks player connection state.

This entity manages the connection lifecycle for players,
including WebSocket associations and connection status.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from domain.value_objects.identifiers import PlayerId, RoomId
from domain.value_objects.connection_status import ConnectionStatus


@dataclass
class PlayerConnection:
    """
    Tracks player connection state.

    This entity manages connection information independently from
    the Player entity to maintain separation of concerns.
    """

    player_id: PlayerId
    room_id: RoomId
    status: ConnectionStatus = ConnectionStatus.CONNECTED
    websocket_id: Optional[str] = None
    last_activity: datetime = field(default_factory=datetime.utcnow)
    disconnect_count: int = 0
    connection_count: int = 1

    def disconnect(self) -> None:
        """
        Handle disconnection.

        Updates status and clears websocket association.
        """
        self.status = ConnectionStatus.DISCONNECTED
        self.websocket_id = None
        self.disconnect_count += 1

    def start_reconnecting(self) -> None:
        """Mark connection as reconnecting."""
        self.status = ConnectionStatus.RECONNECTING

    def reconnect(self, websocket_id: str) -> None:
        """
        Handle reconnection.

        Args:
            websocket_id: New WebSocket identifier
        """
        self.status = ConnectionStatus.CONNECTED
        self.websocket_id = websocket_id
        self.last_activity = datetime.utcnow()
        self.connection_count += 1

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()

    def is_active(self, timeout_seconds: int = 60) -> bool:
        """
        Check if connection is considered active.

        Args:
            timeout_seconds: Seconds before considering inactive

        Returns:
            True if connection is active within timeout
        """
        if self.status != ConnectionStatus.CONNECTED:
            return False

        elapsed = (datetime.utcnow() - self.last_activity).total_seconds()
        return elapsed < timeout_seconds

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "player_id": str(self.player_id),
            "room_id": str(self.room_id),
            "status": self.status.value,
            "websocket_id": self.websocket_id,
            "last_activity": self.last_activity.isoformat(),
            "disconnect_count": self.disconnect_count,
            "connection_count": self.connection_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PlayerConnection":
        """Create from dictionary."""
        return cls(
            player_id=PlayerId(data["player_id"]),
            room_id=RoomId(data["room_id"]),
            status=ConnectionStatus(data["status"]),
            websocket_id=data.get("websocket_id"),
            last_activity=datetime.fromisoformat(data["last_activity"]),
            disconnect_count=data.get("disconnect_count", 0),
            connection_count=data.get("connection_count", 1),
        )
