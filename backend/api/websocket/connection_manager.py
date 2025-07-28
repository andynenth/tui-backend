# backend/api/websocket/connection_manager.py

"""
Player Connection Tracking System

Manages player connection states, disconnection tracking, and reconnection windows.
Works alongside the existing SocketManager for WebSocket management.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ConnectionStatus(Enum):
    """Player connection states"""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"


@dataclass
class PlayerConnection:
    """Represents a player's connection state"""

    player_name: str
    room_id: str
    connection_status: ConnectionStatus = ConnectionStatus.CONNECTED
    disconnect_time: Optional[datetime] = None
    original_is_bot: bool = False
    websocket_id: Optional[str] = None  # To track specific connections


class ConnectionManager:
    """Manages player connections and disconnection tracking"""

    def __init__(self):
        # Track connections by room_id -> player_name -> PlayerConnection
        self.connections: Dict[str, Dict[str, PlayerConnection]] = {}
        # Track websocket to player mapping
        self.websocket_to_player: Dict[str, tuple[str, str]] = (
            {}
        )  # ws_id -> (room_id, player_name)
        # Lock for thread-safe operations
        self.lock = asyncio.Lock()

    async def register_player(
        self, room_id: str, player_name: str, websocket_id: str
    ) -> None:
        """Register a player connection"""
        async with self.lock:
            if room_id not in self.connections:
                self.connections[room_id] = {}

            # Check if player was disconnected and reconnecting
            if player_name in self.connections[room_id]:
                connection = self.connections[room_id][player_name]
                if connection.connection_status == ConnectionStatus.DISCONNECTED:
                    # Always allow reconnection (unlimited reconnection time)
                    connection.connection_status = ConnectionStatus.CONNECTED
                    connection.disconnect_time = None
                    connection.websocket_id = websocket_id
                    logger.info(f"Player {player_name} reconnected to room {room_id}")
            else:
                # New connection
                self.connections[room_id][player_name] = PlayerConnection(
                    player_name=player_name,
                    room_id=room_id,
                    connection_status=ConnectionStatus.CONNECTED,
                    websocket_id=websocket_id,
                )
                logger.info(f"Player {player_name} connected to room {room_id}")

            # Update websocket mapping
            self.websocket_to_player[websocket_id] = (room_id, player_name)

    async def handle_disconnect(self, websocket_id: str) -> Optional[PlayerConnection]:
        """Handle player disconnection"""
        async with self.lock:
            # Find player from websocket ID
            if websocket_id not in self.websocket_to_player:
                logger.warning(
                    f"WebSocket ID {websocket_id} not found in mapping. Current mappings: {list(self.websocket_to_player.keys())}"
                )
                return None

            room_id, player_name = self.websocket_to_player[websocket_id]

            # Remove websocket mapping
            del self.websocket_to_player[websocket_id]

            # Update connection state
            if room_id in self.connections and player_name in self.connections[room_id]:
                connection = self.connections[room_id][player_name]
                connection.connection_status = ConnectionStatus.DISCONNECTED
                connection.disconnect_time = datetime.now()
                connection.websocket_id = None

                logger.info(
                    f"Player {player_name} disconnected from room {room_id}. "
                    f"Can reconnect anytime while game is active."
                )

                return connection

            return None

    async def check_reconnection(self, room_id: str, player_name: str) -> bool:
        """Check if a player is reconnecting"""
        async with self.lock:
            if room_id in self.connections and player_name in self.connections[room_id]:
                connection = self.connections[room_id][player_name]
                return connection.connection_status == ConnectionStatus.DISCONNECTED
            return False

    async def get_connection(
        self, room_id: str, player_name: str
    ) -> Optional[PlayerConnection]:
        """Get a player's connection info"""
        async with self.lock:
            if room_id in self.connections and player_name in self.connections[room_id]:
                return self.connections[room_id][player_name]
            return None
    
    def get_connection_by_websocket_id(self, websocket_id: str) -> Optional[PlayerConnection]:
        """Get a player's connection info by websocket ID (synchronous for compatibility)"""
        # No lock needed for read operation
        if websocket_id not in self.websocket_to_player:
            return None
        
        room_id, player_name = self.websocket_to_player[websocket_id]
        
        if room_id in self.connections and player_name in self.connections[room_id]:
            connection = self.connections[room_id][player_name]
            # Create a simple object with the needed attributes
            class SimpleConnection:
                def __init__(self, player_id, player_name):
                    self.player_id = player_id
                    self.player_name = player_name
            
            # Generate player_id from room and name
            player_id = f"{room_id}_p{hash(player_name) % 100}"
            return SimpleConnection(player_id, player_name)
        
        return None

    async def get_disconnected_players(
        self, room_id: str
    ) -> Dict[str, PlayerConnection]:
        """Get all disconnected players in a room"""
        async with self.lock:
            if room_id not in self.connections:
                return {}

            return {
                player_name: conn
                for player_name, conn in self.connections[room_id].items()
                if conn.connection_status == ConnectionStatus.DISCONNECTED
            }

    async def remove_connection(self, room_id: str, player_name: str) -> None:
        """Remove a player connection (e.g., when leaving room)"""
        async with self.lock:
            if room_id in self.connections and player_name in self.connections[room_id]:
                connection = self.connections[room_id][player_name]

                # Remove websocket mapping if exists
                if (
                    connection.websocket_id
                    and connection.websocket_id in self.websocket_to_player
                ):
                    del self.websocket_to_player[connection.websocket_id]

                # Remove connection
                del self.connections[room_id][player_name]

                # Clean up empty rooms
                if not self.connections[room_id]:
                    del self.connections[room_id]

                logger.info(
                    f"Removed connection for player {player_name} from room {room_id}"
                )

    async def cleanup_room(self, room_id: str) -> None:
        """Clean up all connections for a room"""
        async with self.lock:
            if room_id in self.connections:
                # Remove all websocket mappings for this room
                ws_ids_to_remove = [
                    ws_id
                    for ws_id, (r_id, _) in self.websocket_to_player.items()
                    if r_id == room_id
                ]
                for ws_id in ws_ids_to_remove:
                    del self.websocket_to_player[ws_id]

                # Remove room connections
                del self.connections[room_id]
                logger.info(f"Cleaned up all connections for room {room_id}")

    # Cleanup task removed - unlimited reconnection time means no expiration

    def get_stats(self) -> dict:
        """Get connection statistics"""
        total_connections = 0
        disconnected_count = 0
        rooms_with_disconnects = 0

        for room_id, room_connections in self.connections.items():
            room_has_disconnect = False
            for connection in room_connections.values():
                total_connections += 1
                if connection.connection_status == ConnectionStatus.DISCONNECTED:
                    disconnected_count += 1
                    room_has_disconnect = True

            if room_has_disconnect:
                rooms_with_disconnects += 1

        return {
            "total_connections": total_connections,
            "connected_players": total_connections - disconnected_count,
            "disconnected_players": disconnected_count,
            "rooms_with_disconnects": rooms_with_disconnects,
            "total_rooms": len(self.connections),
        }


# Create singleton instance
connection_manager = ConnectionManager()
