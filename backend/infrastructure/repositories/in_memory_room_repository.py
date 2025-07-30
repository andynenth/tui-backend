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

    async def list_active(self, limit: int = 100) -> List[Room]:
        """
        Get list of active rooms (not completed/abandoned).

        Args:
            limit: Maximum number of rooms to return

        Returns:
            List of active rooms
        """
        active_rooms = []
        for room in self._rooms.values():
            # Include rooms that are WAITING, READY, or IN_GAME
            if room.status.value in ["WAITING", "READY", "IN_GAME"]:
                active_rooms.append(room)
                if len(active_rooms) >= limit:
                    break
        return active_rooms

    async def find_by_player(self, player_id: str) -> Optional[Room]:
        """
        Find a room containing a player by ID.

        Args:
            player_id: ID of the player (e.g., "room123_p0")

        Returns:
            Room containing the player, None if not found
        """
        # Extract room_id from player_id format
        if "_p" in player_id:
            room_id = player_id.split("_p")[0]
            room = self._rooms.get(room_id)
            if room:
                # Verify the player is actually in this room
                try:
                    slot_index = int(player_id.split("_p")[1])
                    if 0 <= slot_index < len(room.slots) and room.slots[slot_index]:
                        return room
                except (IndexError, ValueError):
                    pass

        # Fallback: search all rooms
        for room in self._rooms.values():
            for i, slot in enumerate(room.slots):
                if slot and f"{room.room_id}_p{i}" == player_id:
                    return room
        return None
