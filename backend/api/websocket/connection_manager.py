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
    reconnect_deadline: Optional[datetime] = None
    original_is_bot: bool = False
    websocket_id: Optional[str] = None  # To track specific connections
    
    def is_within_grace_period(self) -> bool:
        """Check if player is still within reconnection grace period"""
        if self.reconnect_deadline is None:
            return False
        return datetime.now() < self.reconnect_deadline
    
    def time_until_deadline(self) -> Optional[timedelta]:
        """Get time remaining until reconnection deadline"""
        if self.reconnect_deadline is None:
            return None
        remaining = self.reconnect_deadline - datetime.now()
        return remaining if remaining.total_seconds() > 0 else timedelta(0)


class ConnectionManager:
    """Manages player connections and disconnection tracking"""
    
    def __init__(self, reconnect_window_seconds: int = 30):
        self.reconnect_window_seconds = reconnect_window_seconds
        # Track connections by room_id -> player_name -> PlayerConnection
        self.connections: Dict[str, Dict[str, PlayerConnection]] = {}
        # Track websocket to player mapping
        self.websocket_to_player: Dict[str, tuple[str, str]] = {}  # ws_id -> (room_id, player_name)
        # Lock for thread-safe operations
        self.lock = asyncio.Lock()
        # Cleanup task (will be created on first use)
        self._cleanup_task = None
    
    async def register_player(self, room_id: str, player_name: str, websocket_id: str) -> None:
        """Register a player connection"""
        # Start cleanup task on first use
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_connections())
        
        async with self.lock:
            if room_id not in self.connections:
                self.connections[room_id] = {}
            
            # Check if player was disconnected and reconnecting
            if player_name in self.connections[room_id]:
                connection = self.connections[room_id][player_name]
                if connection.connection_status == ConnectionStatus.DISCONNECTED:
                    if connection.is_within_grace_period():
                        # Reconnection within grace period
                        connection.connection_status = ConnectionStatus.CONNECTED
                        connection.disconnect_time = None
                        connection.reconnect_deadline = None
                        connection.websocket_id = websocket_id
                        logger.info(f"Player {player_name} reconnected to room {room_id} within grace period")
                    else:
                        # Grace period expired, treat as new connection
                        connection.connection_status = ConnectionStatus.CONNECTED
                        connection.disconnect_time = None
                        connection.reconnect_deadline = None
                        connection.websocket_id = websocket_id
                        logger.info(f"Player {player_name} reconnected to room {room_id} after grace period expired")
            else:
                # New connection
                self.connections[room_id][player_name] = PlayerConnection(
                    player_name=player_name,
                    room_id=room_id,
                    connection_status=ConnectionStatus.CONNECTED,
                    websocket_id=websocket_id
                )
                logger.info(f"Player {player_name} connected to room {room_id}")
            
            # Update websocket mapping
            self.websocket_to_player[websocket_id] = (room_id, player_name)
    
    async def handle_disconnect(self, websocket_id: str) -> Optional[PlayerConnection]:
        """Handle player disconnection"""
        async with self.lock:
            # Find player from websocket ID
            if websocket_id not in self.websocket_to_player:
                return None
            
            room_id, player_name = self.websocket_to_player[websocket_id]
            
            # Remove websocket mapping
            del self.websocket_to_player[websocket_id]
            
            # Update connection state
            if room_id in self.connections and player_name in self.connections[room_id]:
                connection = self.connections[room_id][player_name]
                connection.connection_status = ConnectionStatus.DISCONNECTED
                connection.disconnect_time = datetime.now()
                connection.reconnect_deadline = datetime.now() + timedelta(seconds=self.reconnect_window_seconds)
                connection.websocket_id = None
                
                logger.info(f"Player {player_name} disconnected from room {room_id}. "
                          f"Grace period until {connection.reconnect_deadline}")
                
                return connection
            
            return None
    
    async def check_reconnection(self, room_id: str, player_name: str) -> bool:
        """Check if a player is reconnecting within grace period"""
        async with self.lock:
            if room_id in self.connections and player_name in self.connections[room_id]:
                connection = self.connections[room_id][player_name]
                return (connection.connection_status == ConnectionStatus.DISCONNECTED and 
                        connection.is_within_grace_period())
            return False
    
    async def get_connection(self, room_id: str, player_name: str) -> Optional[PlayerConnection]:
        """Get a player's connection info"""
        async with self.lock:
            if room_id in self.connections and player_name in self.connections[room_id]:
                return self.connections[room_id][player_name]
            return None
    
    async def get_disconnected_players(self, room_id: str) -> Dict[str, PlayerConnection]:
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
                if connection.websocket_id and connection.websocket_id in self.websocket_to_player:
                    del self.websocket_to_player[connection.websocket_id]
                
                # Remove connection
                del self.connections[room_id][player_name]
                
                # Clean up empty rooms
                if not self.connections[room_id]:
                    del self.connections[room_id]
                
                logger.info(f"Removed connection for player {player_name} from room {room_id}")
    
    async def cleanup_room(self, room_id: str) -> None:
        """Clean up all connections for a room"""
        async with self.lock:
            if room_id in self.connections:
                # Remove all websocket mappings for this room
                ws_ids_to_remove = [
                    ws_id for ws_id, (r_id, _) in self.websocket_to_player.items()
                    if r_id == room_id
                ]
                for ws_id in ws_ids_to_remove:
                    del self.websocket_to_player[ws_id]
                
                # Remove room connections
                del self.connections[room_id]
                logger.info(f"Cleaned up all connections for room {room_id}")
    
    async def _cleanup_expired_connections(self) -> None:
        """Background task to clean up expired disconnected connections"""
        while True:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds
                
                async with self.lock:
                    current_time = datetime.now()
                    expired_connections = []
                    
                    # Find expired connections
                    for room_id, room_connections in self.connections.items():
                        for player_name, connection in room_connections.items():
                            if (connection.connection_status == ConnectionStatus.DISCONNECTED and
                                connection.reconnect_deadline and
                                current_time > connection.reconnect_deadline):
                                expired_connections.append((room_id, player_name))
                    
                    # Remove expired connections
                    for room_id, player_name in expired_connections:
                        if room_id in self.connections and player_name in self.connections[room_id]:
                            logger.info(f"Removing expired connection for {player_name} in room {room_id}")
                            del self.connections[room_id][player_name]
                            
                            # Clean up empty rooms
                            if not self.connections[room_id]:
                                del self.connections[room_id]
                
            except Exception as e:
                logger.error(f"Error in connection cleanup task: {e}")
    
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
            "total_rooms": len(self.connections)
        }
    
    def __del__(self):
        """Cleanup when manager is destroyed"""
        if hasattr(self, '_cleanup_task') and self._cleanup_task:
            self._cleanup_task.cancel()


# Create singleton instance
connection_manager = ConnectionManager()