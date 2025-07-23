# infrastructure/websocket/connection_manager.py
"""
Manages WebSocket connections and their associations.
"""

import logging
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class ConnectionInfo:
    """Information about a WebSocket connection."""
    connection: Any  # WebSocket connection object
    player_id: str
    player_name: str
    room_id: Optional[str] = None
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_ping: datetime = field(default_factory=datetime.utcnow)
    
    def is_stale(self, timeout_seconds: int = 60) -> bool:
        """Check if connection is stale."""
        return (datetime.utcnow() - self.last_ping).total_seconds() > timeout_seconds


class ConnectionManager:
    """
    Manages WebSocket connections and their associations.
    
    This class handles:
    - Connection registration/unregistration
    - Player to connection mapping
    - Room to connections mapping
    - Connection health tracking
    """
    
    def __init__(self):
        # Maps
        self._connections: Dict[str, ConnectionInfo] = {}  # player_id -> ConnectionInfo
        self._connection_to_player: Dict[Any, str] = {}  # connection -> player_id
        self._room_connections: Dict[str, Set[str]] = {}  # room_id -> set of player_ids
        
        # Locks for thread safety
        self._lock = asyncio.Lock()
        
        # Stats
        self._total_connections = 0
        self._total_disconnections = 0
    
    async def register_connection(
        self,
        connection,
        player_id: str,
        player_name: str,
        room_id: Optional[str] = None
    ) -> bool:
        """
        Register a new WebSocket connection.
        
        Args:
            connection: WebSocket connection object
            player_id: Unique player identifier
            player_name: Player display name
            room_id: Optional room the player is in
            
        Returns:
            True if registration successful
        """
        async with self._lock:
            try:
                # Check if player already has a connection
                if player_id in self._connections:
                    old_connection = self._connections[player_id].connection
                    if old_connection != connection:
                        logger.warning(
                            f"Player {player_id} already connected, closing old connection"
                        )
                        # Remove old connection
                        await self._unregister_connection_internal(old_connection)
                
                # Create connection info
                info = ConnectionInfo(
                    connection=connection,
                    player_id=player_id,
                    player_name=player_name,
                    room_id=room_id
                )
                
                # Register connection
                self._connections[player_id] = info
                self._connection_to_player[connection] = player_id
                
                # Add to room if specified
                if room_id:
                    if room_id not in self._room_connections:
                        self._room_connections[room_id] = set()
                    self._room_connections[room_id].add(player_id)
                
                self._total_connections += 1
                
                logger.info(
                    f"Registered connection for {player_name} ({player_id}) "
                    f"in room {room_id}"
                )
                
                return True
                
            except Exception as e:
                logger.error(
                    f"Failed to register connection: {str(e)}",
                    exc_info=True
                )
                return False
    
    async def unregister_connection(self, connection) -> Optional[str]:
        """
        Unregister a WebSocket connection.
        
        Args:
            connection: WebSocket connection object
            
        Returns:
            Player ID if connection was registered
        """
        async with self._lock:
            return await self._unregister_connection_internal(connection)
    
    async def _unregister_connection_internal(self, connection) -> Optional[str]:
        """Internal method to unregister connection without lock."""
        player_id = self._connection_to_player.get(connection)
        
        if not player_id:
            return None
        
        # Get connection info
        info = self._connections.get(player_id)
        if not info:
            return None
        
        # Remove from room
        if info.room_id and info.room_id in self._room_connections:
            self._room_connections[info.room_id].discard(player_id)
            if not self._room_connections[info.room_id]:
                del self._room_connections[info.room_id]
        
        # Remove connection
        del self._connections[player_id]
        del self._connection_to_player[connection]
        
        self._total_disconnections += 1
        
        logger.info(
            f"Unregistered connection for {info.player_name} ({player_id})"
        )
        
        return player_id
    
    def get_connection(self, player_id: str) -> Optional[Any]:
        """Get connection object for a player."""
        info = self._connections.get(player_id)
        return info.connection if info else None
    
    def get_connection_info(self, player_id: str) -> Optional[ConnectionInfo]:
        """Get full connection info for a player."""
        return self._connections.get(player_id)
    
    def is_connected(self, player_id: str) -> bool:
        """Check if a player is connected."""
        return player_id in self._connections
    
    async def update_player_room(
        self,
        player_id: str,
        new_room_id: Optional[str]
    ) -> bool:
        """
        Update the room association for a player.
        
        Args:
            player_id: The player ID
            new_room_id: New room ID (None to leave room)
            
        Returns:
            True if update successful
        """
        async with self._lock:
            info = self._connections.get(player_id)
            if not info:
                return False
            
            # Remove from old room
            if info.room_id and info.room_id in self._room_connections:
                self._room_connections[info.room_id].discard(player_id)
                if not self._room_connections[info.room_id]:
                    del self._room_connections[info.room_id]
            
            # Add to new room
            if new_room_id:
                if new_room_id not in self._room_connections:
                    self._room_connections[new_room_id] = set()
                self._room_connections[new_room_id].add(player_id)
            
            # Update info
            info.room_id = new_room_id
            
            return True
    
    def get_room_connections(self, room_id: str) -> List[str]:
        """Get list of player IDs connected in a room."""
        return list(self._room_connections.get(room_id, set()))
    
    def get_room_connections_objects(self, room_id: str) -> List[Any]:
        """Get list of connection objects for a room."""
        player_ids = self._room_connections.get(room_id, set())
        connections = []
        
        for player_id in player_ids:
            info = self._connections.get(player_id)
            if info:
                connections.append(info.connection)
        
        return connections
    
    def get_all_connections(self) -> List[Any]:
        """Get all active connection objects."""
        return [info.connection for info in self._connections.values()]
    
    async def ping_connection(self, player_id: str) -> bool:
        """
        Update last ping time for a connection.
        
        Args:
            player_id: The player ID
            
        Returns:
            True if connection exists
        """
        info = self._connections.get(player_id)
        if info:
            info.last_ping = datetime.utcnow()
            return True
        return False
    
    async def cleanup_stale_connections(self, timeout_seconds: int = 60) -> List[str]:
        """
        Remove stale connections.
        
        Args:
            timeout_seconds: Seconds before considering connection stale
            
        Returns:
            List of removed player IDs
        """
        async with self._lock:
            stale_players = []
            
            for player_id, info in list(self._connections.items()):
                if info.is_stale(timeout_seconds):
                    stale_players.append(player_id)
                    await self._unregister_connection_internal(info.connection)
            
            if stale_players:
                logger.info(f"Cleaned up {len(stale_players)} stale connections")
            
            return stale_players
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        return {
            "active_connections": len(self._connections),
            "active_rooms": len(self._room_connections),
            "total_connections": self._total_connections,
            "total_disconnections": self._total_disconnections,
            "rooms": {
                room_id: len(players)
                for room_id, players in self._room_connections.items()
            }
        }