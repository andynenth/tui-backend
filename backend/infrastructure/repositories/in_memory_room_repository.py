"""
In-memory implementation of the RoomRepository interface.

This provides a simple in-memory storage for rooms during development
and testing. In production, this would be replaced with a persistent store.
"""

from typing import Optional, List, Dict
from domain.entities.room import Room
from domain.interfaces.repositories import RoomRepository


class InMemoryRoomRepository(RoomRepository):
    """In-memory implementation of room repository."""
    
    def __init__(self):
        """Initialize with empty storage."""
        self._rooms: Dict[str, Room] = {}
    
    async def save(self, room: Room) -> None:
        """
        Save or update a room.
        
        Args:
            room: Room aggregate to persist
        """
        self._rooms[room.room_id] = room
    
    async def find_by_id(self, room_id: str) -> Optional[Room]:
        """
        Find a room by its ID.
        
        Args:
            room_id: Unique room identifier
            
        Returns:
            Room if found, None otherwise
        """
        return self._rooms.get(room_id)
    
    async def find_all(self) -> List[Room]:
        """
        Get all rooms.
        
        Returns:
            List of all rooms
        """
        return list(self._rooms.values())
    
    async def find_by_player_name(self, player_name: str) -> Optional[Room]:
        """
        Find a room containing a specific player.
        
        Args:
            player_name: Name of the player
            
        Returns:
            Room containing the player, None if not found
        """
        for room in self._rooms.values():
            if any(p and p.name == player_name for p in room.slots):
                return room
        return None
    
    async def delete(self, room_id: str) -> bool:
        """
        Delete a room.
        
        Args:
            room_id: ID of room to delete
            
        Returns:
            True if deleted, False if not found
        """
        if room_id in self._rooms:
            del self._rooms[room_id]
            return True
        return False
    
    async def exists(self, room_id: str) -> bool:
        """
        Check if a room exists.
        
        Args:
            room_id: ID to check
            
        Returns:
            True if exists, False otherwise
        """
        return room_id in self._rooms