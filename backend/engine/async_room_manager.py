# backend/engine/async_room_manager.py
"""
Async implementation of RoomManager for Phase 2 migration.
This will eventually replace the sync RoomManager.
"""

import asyncio
import uuid
import logging
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime

from .async_room import AsyncRoom

logger = logging.getLogger(__name__)


@dataclass
class RoomCreationResult:
    """Result of room creation operation."""
    room_id: str
    room: AsyncRoom
    created_at: datetime
    host_name: str


class AsyncRoomManager:
    """
    Async version of RoomManager.
    Manages all active game rooms with async operations for future database integration.
    """
    
    def __init__(self):
        """Initialize the AsyncRoomManager."""
        self.rooms: Dict[str, AsyncRoom] = {}
        self._manager_lock = asyncio.Lock()  # For operations that modify rooms dict
        self._room_creation_lock = asyncio.Lock()  # For room ID generation
        self._stats = {
            "rooms_created": 0,
            "rooms_deleted": 0,
            "total_operations": 0
        }
        logger.info("AsyncRoomManager initialized")
    
    async def create_room(self, host_name: str) -> str:
        """
        Create a new game room asynchronously.
        
        Args:
            host_name: The name of the player who will be the host
            
        Returns:
            str: The ID of the newly created room
            
        Future: Will persist room creation to database
        """
        async with self._room_creation_lock:
            # Generate unique room ID
            room_id = await self._generate_unique_room_id()
            
            # Create async room
            room = AsyncRoom(room_id, host_name)
            
            # Add to rooms dict with lock
            async with self._manager_lock:
                self.rooms[room_id] = room
                self._stats["rooms_created"] += 1
                self._stats["total_operations"] += 1
            
            logger.info(f"Created async room {room_id} with host {host_name}")
            
            # Future: await self._persist_room_creation(room_id, host_name)
            
            return room_id
    
    async def get_room(self, room_id: str) -> Optional[AsyncRoom]:
        """
        Retrieve a room by its ID asynchronously.
        
        Args:
            room_id: The ID of the room to retrieve
            
        Returns:
            Optional[AsyncRoom]: The room if found, None otherwise
            
        Future: May need to fetch from database if not in memory
        """
        # No lock needed for read operation
        room = self.rooms.get(room_id)
        
        if room:
            self._stats["total_operations"] += 1
            return room
        
        # Future: Check database if not in memory
        # room = await self._fetch_room_from_db(room_id)
        
        return None
    
    async def delete_room(self, room_id: str) -> bool:
        """
        Delete a room from the manager asynchronously.
        
        Args:
            room_id: The ID of the room to delete
            
        Returns:
            bool: True if room was deleted, False if not found
            
        Future: Will persist deletion to database
        """
        async with self._manager_lock:
            if room_id in self.rooms:
                room = self.rooms[room_id]
                
                # Clean up room resources
                await room.cleanup()
                
                # Remove from dict
                del self.rooms[room_id]
                self._stats["rooms_deleted"] += 1
                self._stats["total_operations"] += 1
                
                logger.info(f"Deleted room {room_id}")
                
                # Future: await self._persist_room_deletion(room_id)
                
                return True
            
            logger.warning(f"Attempted to delete non-existent room {room_id}")
            return False
    
    async def list_rooms(self) -> List[Dict]:
        """
        List all available rooms asynchronously.
        
        Returns:
            List[Dict]: List of room summaries for available rooms
            
        Future: May paginate results from database
        """
        available_rooms = []
        
        # Create snapshot to avoid holding lock during summary generation
        async with self._manager_lock:
            room_snapshot = list(self.rooms.values())
        
        # Generate summaries without lock
        for room in room_snapshot:
            if not room.started:
                summary = await room.summary()
                available_rooms.append(summary)
        
        self._stats["total_operations"] += 1
        
        return available_rooms
    
    async def get_room_count(self) -> int:
        """Get total number of active rooms."""
        return len(self.rooms)
    
    async def get_stats(self) -> Dict:
        """Get manager statistics."""
        async with self._manager_lock:
            return {
                **self._stats,
                "active_rooms": len(self.rooms),
                "started_games": sum(1 for r in self.rooms.values() if r.started)
            }
    
    async def cleanup_empty_rooms(self) -> int:
        """
        Clean up rooms with no human players.
        
        Returns:
            int: Number of rooms cleaned up
        """
        rooms_to_delete = []
        
        # Identify empty rooms
        async with self._manager_lock:
            for room_id, room in self.rooms.items():
                if await room.is_empty():
                    rooms_to_delete.append(room_id)
        
        # Delete empty rooms
        deleted_count = 0
        for room_id in rooms_to_delete:
            if await self.delete_room(room_id):
                deleted_count += 1
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} empty rooms")
        
        return deleted_count
    
    async def _generate_unique_room_id(self) -> str:
        """
        Generate a unique room ID.
        
        Returns:
            str: A unique 6-character room ID
        """
        max_attempts = 100
        
        for _ in range(max_attempts):
            room_id = uuid.uuid4().hex[:6].upper()
            
            # Check uniqueness
            if room_id not in self.rooms:
                # Future: Also check database
                # if not await self._room_exists_in_db(room_id):
                return room_id
        
        # Fallback to longer ID if needed
        return uuid.uuid4().hex[:8].upper()
    
    # Compatibility methods for migration
    def create_room_sync(self, host_name: str) -> str:
        """Sync wrapper for create_room (for migration compatibility)."""
        import asyncio
        try:
            # Try to get the running loop
            loop = asyncio.get_running_loop()
            # We're in an async context, can't use run_until_complete
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.create_room(host_name))
                return future.result()
        except RuntimeError:
            # No running loop, safe to create new one
            return asyncio.run(self.create_room(host_name))
    
    def get_room_sync(self, room_id: str) -> Optional[AsyncRoom]:
        """Sync wrapper for get_room (for migration compatibility)."""
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.get_room(room_id))
                return future.result()
        except RuntimeError:
            return asyncio.run(self.get_room(room_id))
    
    def delete_room_sync(self, room_id: str) -> bool:
        """Sync wrapper for delete_room (for migration compatibility)."""
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.delete_room(room_id))
                return future.result()
        except RuntimeError:
            return asyncio.run(self.delete_room(room_id))
    
    def list_rooms_sync(self) -> List[Dict]:
        """Sync wrapper for list_rooms (for migration compatibility)."""
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.list_rooms())
                return future.result()
        except RuntimeError:
            return asyncio.run(self.list_rooms())