"""
High-performance in-memory room repository with optimization features.

This implementation provides O(1) lookups, thread-safe operations, and
memory management suitable for real-time multiplayer gaming.
"""

import asyncio
import time
from typing import Optional, List, Dict, Set
from collections import OrderedDict
from copy import deepcopy

from application.interfaces.repositories import RoomRepository
from domain.entities.room import Room
from domain.value_objects import RoomStatus


class OptimizedRoomRepository(RoomRepository):
    """
    High-performance in-memory room repository with:
    - O(1) lookups by ID and code
    - Thread-safe operations with asyncio locks
    - Memory management with LRU eviction
    - Real-time access metrics
    """
    
    def __init__(self, max_rooms: int = 10000):
        """
        Initialize repository with performance features.
        
        Args:
            max_rooms: Maximum number of rooms to keep in memory
        """
        # Primary storage with LRU ordering
        self._rooms: OrderedDict[str, Room] = OrderedDict()
        
        # Secondary indexes for fast lookups
        self._code_index: Dict[str, str] = {}  # code -> room_id
        self._player_index: Dict[str, Set[str]] = {}  # player_id -> set of room_ids
        
        # Locks for thread safety
        self._locks: Dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()
        
        # Performance metrics
        self._access_count: Dict[str, int] = {}
        self._last_access: Dict[str, float] = {}
        
        # Memory management
        self._max_rooms = max_rooms
        self._completed_rooms: List[Room] = []  # For archival
        
    async def get_by_id(self, room_id: str) -> Optional[Room]:
        """Get room by ID with O(1) performance."""
        if room_id in self._rooms:
            # Update access metrics
            self._access_count[room_id] = self._access_count.get(room_id, 0) + 1
            self._last_access[room_id] = time.time()
            
            # Move to end for LRU
            self._rooms.move_to_end(room_id)
            
            return self._rooms[room_id]
        return None
    
    async def get_by_code(self, room_code: str) -> Optional[Room]:
        """Get room by join code with O(1) performance."""
        room_id = self._code_index.get(room_code)
        if room_id:
            return await self.get_by_id(room_id)
        return None
    
    async def save(self, room: Room) -> None:
        """Save room with automatic memory management."""
        async with self._get_lock(room.room_id):
            # Check memory pressure
            if len(self._rooms) >= self._max_rooms:
                await self._evict_completed_rooms()
            
            # Update primary storage
            is_new = room.room_id not in self._rooms
            self._rooms[room.room_id] = room
            self._rooms.move_to_end(room.room_id)
            
            # Update indexes
            if hasattr(room, 'join_code') and room.join_code:
                self._code_index[room.join_code] = room.room_id
            
            # Update player index
            if is_new:
                await self._update_player_index(room)
            
            # Check if room is completed for archival
            if room.status == RoomStatus.COMPLETED:
                self._completed_rooms.append(deepcopy(room))
    
    async def delete(self, room_id: str) -> None:
        """Delete room and clean up indexes."""
        async with self._get_lock(room_id):
            if room_id in self._rooms:
                room = self._rooms[room_id]
                
                # Archive if completed
                if room.status == RoomStatus.COMPLETED:
                    self._completed_rooms.append(deepcopy(room))
                
                # Clean up indexes
                if hasattr(room, 'join_code') and room.join_code:
                    self._code_index.pop(room.join_code, None)
                
                # Clean up player index
                for player in room.players:
                    if player and player.id.value in self._player_index:
                        self._player_index[player.id.value].discard(room_id)
                
                # Remove from storage
                del self._rooms[room_id]
                self._access_count.pop(room_id, None)
                self._last_access.pop(room_id, None)
                self._locks.pop(room_id, None)
    
    async def list_active(self, limit: int = 100) -> List[Room]:
        """List active rooms sorted by recent activity."""
        active_rooms = []
        
        # Iterate in LRU order (most recent first)
        for room in reversed(self._rooms.values()):
            if room.status in [RoomStatus.WAITING, RoomStatus.IN_GAME]:
                active_rooms.append(room)
                if len(active_rooms) >= limit:
                    break
        
        return active_rooms
    
    async def find_by_player(self, player_id: str) -> Optional[Room]:
        """Find room by player with O(1) index lookup."""
        room_ids = self._player_index.get(player_id, set())
        
        # Return the most recently accessed room
        for room_id in room_ids:
            if room_id in self._rooms:
                return await self.get_by_id(room_id)
        
        return None
    
    # Performance optimization methods
    
    async def _get_lock(self, room_id: str) -> asyncio.Lock:
        """Get or create a lock for a specific room."""
        async with self._global_lock:
            if room_id not in self._locks:
                self._locks[room_id] = asyncio.Lock()
            return self._locks[room_id]
    
    async def _evict_completed_rooms(self) -> None:
        """Evict completed rooms when at capacity."""
        evicted = 0
        
        # First try to evict completed rooms
        for room_id in list(self._rooms.keys()):
            if self._rooms[room_id].status == RoomStatus.COMPLETED:
                await self.delete(room_id)
                evicted += 1
                if len(self._rooms) < self._max_rooms * 0.9:  # 90% threshold
                    break
        
        # If still over capacity, evict least recently used
        if len(self._rooms) >= self._max_rooms:
            # Get LRU rooms (first items in OrderedDict)
            for room_id in list(self._rooms.keys())[:10]:  # Evict up to 10
                room = self._rooms[room_id]
                if room.status != RoomStatus.IN_GAME:  # Never evict active games
                    await self.delete(room_id)
                    evicted += 1
        
        if evicted > 0:
            import logging
            logging.info(f"Evicted {evicted} rooms due to memory pressure")
    
    async def _update_player_index(self, room: Room) -> None:
        """Update the player index for fast lookups."""
        for player in room.players:
            if player:
                player_id = player.id.value
                if player_id not in self._player_index:
                    self._player_index[player_id] = set()
                self._player_index[player_id].add(room.room_id)
    
    # Archive access methods
    
    def get_completed_rooms(self) -> List[Room]:
        """Get completed rooms for archival."""
        rooms = self._completed_rooms
        self._completed_rooms = []  # Clear after retrieval
        return rooms
    
    # Monitoring methods
    
    def get_metrics(self) -> Dict[str, any]:
        """Get repository performance metrics."""
        return {
            'total_rooms': len(self._rooms),
            'active_rooms': sum(1 for r in self._rooms.values() 
                              if r.status in [RoomStatus.WAITING, RoomStatus.IN_GAME]),
            'completed_rooms': sum(1 for r in self._rooms.values() 
                                 if r.status == RoomStatus.COMPLETED),
            'total_accesses': sum(self._access_count.values()),
            'unique_players': len(self._player_index),
            'memory_usage_estimate': len(self._rooms) * 2048,  # ~2KB per room estimate
            'pending_archival': len(self._completed_rooms)
        }