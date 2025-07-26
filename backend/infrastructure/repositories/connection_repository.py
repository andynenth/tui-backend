"""
In-memory implementation of the connection repository.

This implementation stores player connections in memory and is suitable
for development and testing. In production, this would be replaced with
a persistent store.
"""

from typing import Optional, List, Dict
from datetime import datetime

from domain.entities.connection import PlayerConnection
from domain.value_objects import PlayerId, RoomId, ConnectionStatus
from application.interfaces.repositories import ConnectionRepository


class InMemoryConnectionRepository(ConnectionRepository):
    """
    In-memory implementation of ConnectionRepository.
    
    Stores connections in nested dictionaries for fast lookup by
    room and player.
    """
    
    def __init__(self):
        # Structure: {room_id: {player_name: PlayerConnection}}
        self._connections: Dict[str, Dict[str, PlayerConnection]] = {}
    
    async def get(self, room_id: str, player_name: str) -> Optional[PlayerConnection]:
        """Get connection info for a player."""
        room_connections = self._connections.get(room_id, {})
        return room_connections.get(player_name)
    
    async def save(self, connection: PlayerConnection) -> None:
        """Save connection info."""
        room_id = connection.room_id.value
        player_name = connection.player_id.value
        
        if room_id not in self._connections:
            self._connections[room_id] = {}
        
        # Update last activity
        connection.last_activity = datetime.utcnow()
        
        self._connections[room_id][player_name] = connection
    
    async def delete(self, room_id: str, player_name: str) -> None:
        """Delete connection info."""
        if room_id in self._connections:
            self._connections[room_id].pop(player_name, None)
            
            # Clean up empty room dict
            if not self._connections[room_id]:
                del self._connections[room_id]
    
    async def list_by_room(self, room_id: str) -> List[PlayerConnection]:
        """List all connections for a room."""
        room_connections = self._connections.get(room_id, {})
        return list(room_connections.values())
    
    async def clear_room(self, room_id: str) -> None:
        """Clear all connections for a room."""
        if room_id in self._connections:
            del self._connections[room_id]
    
    async def get_all(self) -> Dict[str, Dict[str, PlayerConnection]]:
        """Get all connections. Useful for debugging."""
        return self._connections.copy()
    
    async def count_by_status(self, status: ConnectionStatus) -> int:
        """Count connections by status."""
        count = 0
        for room_connections in self._connections.values():
            for connection in room_connections.values():
                if connection.status == status:
                    count += 1
        return count
    
    def snapshot(self) -> Dict:
        """Create a snapshot of the current state for rollback."""
        import copy
        return copy.deepcopy(self._connections)
    
    def restore(self, snapshot: Dict) -> None:
        """Restore from a snapshot."""
        import copy
        self._connections = copy.deepcopy(snapshot)