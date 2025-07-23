# infrastructure/persistence/room_repository_impl.py
"""
Implementation of room repository for managing game rooms.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio
import secrets
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Room:
    """Room entity for infrastructure layer."""
    id: str
    join_code: str
    host_name: str
    players: List[str] = field(default_factory=list)
    max_players: int = 4
    game_id: Optional[str] = None
    is_game_finished: bool = True
    is_closed: bool = False
    settings: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_player(self, player_name: str) -> bool:
        """Add a player to the room."""
        if player_name not in self.players and len(self.players) < self.max_players:
            self.players.append(player_name)
            return True
        return False
    
    def remove_player(self, player_name: str) -> bool:
        """Remove a player from the room."""
        if player_name in self.players:
            self.players.remove(player_name)
            return True
        return False
    
    def has_player(self, player_name: str) -> bool:
        """Check if player is in the room."""
        return player_name in self.players
    
    def is_full(self) -> bool:
        """Check if room is full."""
        return len(self.players) >= self.max_players
    
    def player_count(self) -> int:
        """Get number of players in room."""
        return len(self.players)
    
    def get_player_names(self) -> List[str]:
        """Get list of player names."""
        return self.players.copy()


class RoomRepository:
    """
    Repository for managing game rooms.
    
    This is not a domain interface - it's infrastructure specific.
    The application layer will use this through dependency injection.
    """
    
    def __init__(self):
        self._rooms: Dict[str, Room] = {}
        self._join_codes: Dict[str, str] = {}  # join_code -> room_id
        self._room_counter = 0
        self._lock = asyncio.Lock()
    
    def _generate_join_code(self) -> str:
        """Generate a unique join code."""
        while True:
            # Generate 6-character code
            code = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(6))
            if code not in self._join_codes:
                return code
    
    async def create_room(
        self,
        host_id: str,
        host_name: str,
        settings: Optional[Dict[str, Any]] = None
    ) -> Room:
        """
        Create a new room.
        
        Args:
            host_id: Host player ID
            host_name: Host player name
            settings: Room settings
            
        Returns:
            Created room
        """
        async with self._lock:
            self._room_counter += 1
            room_id = f"room_{self._room_counter}"
            join_code = self._generate_join_code()
            
            room = Room(
                id=room_id,
                join_code=join_code,
                host_name=host_name,
                settings=settings or {}
            )
            
            # Store room
            self._rooms[room_id] = room
            self._join_codes[join_code] = room_id
            
            logger.info(f"Created room {room_id} with join code {join_code}")
            
            return room
    
    async def get(self, room_id: str) -> Optional[Room]:
        """Get room by ID."""
        return self._rooms.get(room_id)
    
    async def get_by_join_code(self, join_code: str) -> Optional[Room]:
        """Get room by join code."""
        room_id = self._join_codes.get(join_code.upper())
        if room_id:
            return self._rooms.get(room_id)
        return None
    
    async def save(self, room: Room) -> None:
        """Save/update a room."""
        async with self._lock:
            self._rooms[room.id] = room
            
            # Update join code mapping if needed
            if room.join_code:
                self._join_codes[room.join_code] = room.id
    
    async def delete(self, room_id: str) -> bool:
        """Delete a room."""
        async with self._lock:
            room = self._rooms.get(room_id)
            if not room:
                return False
            
            # Remove join code mapping
            if room.join_code in self._join_codes:
                del self._join_codes[room.join_code]
            
            # Remove room
            del self._rooms[room_id]
            
            logger.info(f"Deleted room {room_id}")
            return True
    
    async def list_public_rooms(self) -> List[Room]:
        """List all public (not closed) rooms."""
        return [
            room for room in self._rooms.values()
            if not room.is_closed
        ]
    
    async def get_player_rooms(self, player_name: str) -> List[Room]:
        """Get all rooms a player is in."""
        return [
            room for room in self._rooms.values()
            if room.has_player(player_name)
        ]
    
    async def cleanup_empty_rooms(self) -> int:
        """
        Clean up empty rooms.
        
        Returns:
            Number of rooms cleaned up
        """
        async with self._lock:
            empty_rooms = [
                room_id for room_id, room in self._rooms.items()
                if room.player_count() == 0 and not room.game_id
            ]
            
            for room_id in empty_rooms:
                room = self._rooms[room_id]
                if room.join_code in self._join_codes:
                    del self._join_codes[room.join_code]
                del self._rooms[room_id]
            
            if empty_rooms:
                logger.info(f"Cleaned up {len(empty_rooms)} empty rooms")
            
            return len(empty_rooms)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get repository statistics."""
        active_rooms = sum(
            1 for room in self._rooms.values()
            if not room.is_closed and room.player_count() > 0
        )
        
        in_game_rooms = sum(
            1 for room in self._rooms.values()
            if room.game_id and not room.is_game_finished
        )
        
        return {
            "total_rooms": len(self._rooms),
            "active_rooms": active_rooms,
            "in_game_rooms": in_game_rooms,
            "empty_rooms": len(self._rooms) - active_rooms,
            "total_players": sum(room.player_count() for room in self._rooms.values())
        }