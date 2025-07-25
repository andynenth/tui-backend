"""
Connection-related domain events.

These events represent WebSocket connection lifecycle changes.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from .base import DomainEvent, GameEvent


@dataclass(frozen=True)
class PlayerConnected(DomainEvent):
    """A player has connected to the system."""
    player_id: str
    websocket_id: str
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            'player_id': self.player_id,
            'websocket_id': self.websocket_id
        }


@dataclass(frozen=True)
class PlayerDisconnected(DomainEvent):
    """A player has disconnected from the system."""
    player_id: str
    websocket_id: str
    reason: Optional[str] = None
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            'player_id': self.player_id,
            'websocket_id': self.websocket_id,
            'reason': self.reason
        }


@dataclass(frozen=True)
class PlayerReconnected(GameEvent):
    """A player has reconnected to their game."""
    player_id: str
    player_name: str
    websocket_id: str
    queued_message_count: int = 0
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'player_id': self.player_id,
            'player_name': self.player_name,
            'websocket_id': self.websocket_id,
            'queued_message_count': self.queued_message_count
        })
        return data


@dataclass(frozen=True)
class ConnectionHeartbeat(DomainEvent):
    """A ping/pong heartbeat was exchanged."""
    websocket_id: str
    client_timestamp: Optional[float] = None
    server_timestamp: float = None
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            'websocket_id': self.websocket_id,
            'client_timestamp': self.client_timestamp,
            'server_timestamp': self.server_timestamp
        }


@dataclass(frozen=True)
class ClientReady(GameEvent):
    """Client has signaled it's ready to receive game events."""
    player_id: str
    player_name: str
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'player_id': self.player_id,
            'player_name': self.player_name
        })
        return data