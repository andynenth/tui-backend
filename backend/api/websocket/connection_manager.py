# backend/api/websocket/connection_manager.py

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, Set

logger = logging.getLogger(__name__)


class ConnectionStatus(Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"


@dataclass
class PlayerConnection:
    """Represents a player's connection state"""
    player_name: str
    room_id: str
    websocket_id: str
    status: ConnectionStatus
    disconnect_time: Optional[datetime] = None
    is_host: bool = False


class ConnectionManager:
    """
    Manages player WebSocket connections and tracks their states.
    Handles disconnections and reconnections without grace period.
    """

    def __init__(self):
        # Map WebSocket ID to PlayerConnection
        self._connections: Dict[str, PlayerConnection] = {}
        # Map (room_id, player_name) to PlayerConnection for quick lookups
        self._player_lookup: Dict[tuple[str, str], PlayerConnection] = {}
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
        logger.info("ConnectionManager initialized")

    async def register_player(self, room_id: str, player_name: str, websocket_id: str) -> None:
        """
        Register a player's WebSocket connection.
        
        Args:
            room_id: The room ID the player is in
            player_name: The player's name
            websocket_id: The unique WebSocket ID
        """
        async with self._lock:
            # Check if player was previously disconnected
            lookup_key = (room_id, player_name)
            existing = self._player_lookup.get(lookup_key)
            
            if existing and existing.status == ConnectionStatus.DISCONNECTED:
                # Player is reconnecting
                logger.info(f"Player {player_name} reconnecting to room {room_id}")
                existing.status = ConnectionStatus.CONNECTED
                existing.websocket_id = websocket_id
                existing.disconnect_time = None
                self._connections[websocket_id] = existing
            else:
                # New connection
                connection = PlayerConnection(
                    player_name=player_name,
                    room_id=room_id,
                    websocket_id=websocket_id,
                    status=ConnectionStatus.CONNECTED
                )
                self._connections[websocket_id] = connection
                self._player_lookup[lookup_key] = connection
                logger.info(f"Player {player_name} registered in room {room_id} with ws_id {websocket_id}")

    async def handle_disconnect(self, websocket_id: str) -> Optional[PlayerConnection]:
        """
        Handle a WebSocket disconnection.
        
        Args:
            websocket_id: The WebSocket ID that disconnected
            
        Returns:
            The PlayerConnection if found, None otherwise
        """
        async with self._lock:
            connection = self._connections.get(websocket_id)
            if not connection:
                logger.warning(f"No connection found for WebSocket ID {websocket_id}")
                return None
            
            # Mark as disconnected
            connection.status = ConnectionStatus.DISCONNECTED
            connection.disconnect_time = datetime.now()
            
            # Remove from active connections but keep in player lookup
            del self._connections[websocket_id]
            
            logger.info(f"Player {connection.player_name} disconnected from room {connection.room_id}")
            return connection

    async def check_reconnection(self, room_id: str, player_name: str) -> bool:
        """
        Check if a player is reconnecting (was previously disconnected).
        
        Args:
            room_id: The room ID
            player_name: The player's name
            
        Returns:
            True if this is a reconnection, False otherwise
        """
        async with self._lock:
            lookup_key = (room_id, player_name)
            connection = self._player_lookup.get(lookup_key)
            return (
                connection is not None and 
                connection.status == ConnectionStatus.DISCONNECTED
            )

    async def get_player_by_websocket(self, websocket_id: str) -> Optional[PlayerConnection]:
        """
        Get player connection info by WebSocket ID.
        
        Args:
            websocket_id: The WebSocket ID
            
        Returns:
            The PlayerConnection if found, None otherwise
        """
        async with self._lock:
            return self._connections.get(websocket_id)

    async def cleanup_room(self, room_id: str) -> None:
        """
        Clean up all connections for a room (when room is deleted).
        
        Args:
            room_id: The room ID to clean up
        """
        async with self._lock:
            # Find all connections for this room
            to_remove = []
            for key, connection in list(self._player_lookup.items()):
                if connection.room_id == room_id:
                    to_remove.append(key)
                    # Also remove from active connections if present
                    if connection.websocket_id in self._connections:
                        del self._connections[connection.websocket_id]
            
            # Remove from player lookup
            for key in to_remove:
                del self._player_lookup[key]
            
            logger.info(f"Cleaned up {len(to_remove)} connections for room {room_id}")

    async def get_room_connections(self, room_id: str) -> Dict[str, ConnectionStatus]:
        """
        Get all player connection statuses for a room.
        
        Args:
            room_id: The room ID
            
        Returns:
            Dict mapping player names to their connection status
        """
        async with self._lock:
            result = {}
            for (rid, player_name), connection in self._player_lookup.items():
                if rid == room_id:
                    result[player_name] = connection.status
            return result

    async def is_player_connected(self, room_id: str, player_name: str) -> bool:
        """
        Check if a player is currently connected.
        
        Args:
            room_id: The room ID
            player_name: The player's name
            
        Returns:
            True if player is connected, False otherwise
        """
        async with self._lock:
            lookup_key = (room_id, player_name)
            connection = self._player_lookup.get(lookup_key)
            return (
                connection is not None and 
                connection.status == ConnectionStatus.CONNECTED
            )

    async def set_host(self, room_id: str, player_name: str) -> None:
        """
        Mark a player as the room host.
        
        Args:
            room_id: The room ID
            player_name: The player's name
        """
        async with self._lock:
            lookup_key = (room_id, player_name)
            connection = self._player_lookup.get(lookup_key)
            if connection:
                connection.is_host = True
                logger.info(f"Player {player_name} set as host for room {room_id}")


# Singleton instance
connection_manager = ConnectionManager()