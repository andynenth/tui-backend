"""
Application layer room repository implementation.

This wraps the domain repository to provide the application layer interface.
"""

from typing import Optional, List, Dict
from copy import deepcopy

from application.interfaces.repositories import RoomRepository as IRoomRepository
from domain.entities.room import Room
from .in_memory_room_repository import InMemoryRoomRepository


class ApplicationRoomRepository(IRoomRepository):
    """
    Adapter that implements the application repository interface
    using the domain repository.
    """

    def __init__(self):
        self._domain_repo = InMemoryRoomRepository()
        self._snapshot_data = None

    async def get_by_id(self, room_id: str) -> Optional[Room]:
        """Get room by ID."""
        return await self._domain_repo.find_by_id(room_id)

    async def get_by_code(self, room_code: str) -> Optional[Room]:
        """Get room by code."""
        # Since room_code == room_id in this implementation,
        # we can delegate to get_by_id
        return await self.get_by_id(room_code)

    async def save(self, room: Room) -> None:
        """Save a room."""
        await self._domain_repo.save(room)

    async def delete(self, room_id: str) -> None:
        """Delete a room."""
        await self._domain_repo.delete(room_id)

    async def list_active(self, limit: int = 100) -> List[Room]:
        """List active rooms."""
        all_rooms = await self._domain_repo.find_all()
        # Filter for active rooms (not completed/abandoned)
        active_rooms = [
            room
            for room in all_rooms
            if room.status.value not in ["COMPLETED", "ABANDONED"]
        ]
        return active_rooms[:limit]

    async def find_by_player(self, player_id: str) -> Optional[Room]:
        """Find room by player."""
        return await self._domain_repo.find_by_player_name(player_id)

    def snapshot(self) -> Dict:
        """Create a snapshot for rollback."""
        # Deep copy the internal state
        self._snapshot_data = deepcopy(self._domain_repo._rooms)
        return {"rooms": self._snapshot_data}

    def restore(self, snapshot: Dict) -> None:
        """Restore from snapshot."""
        if "rooms" in snapshot:
            self._domain_repo._rooms = deepcopy(snapshot["rooms"])
