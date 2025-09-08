# Room Manager Deep Dive - Multiplayer Game Orchestration

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Room Lifecycle](#room-lifecycle)
4. [AsyncRoom Integration](#asyncroom-integration)
5. [Migration Strategy](#migration-strategy)
6. [Lock Management](#lock-management)
7. [Statistics & Monitoring](#statistics--monitoring)
8. [Code Examples](#code-examples)
9. [Testing & Debugging](#testing--debugging)

## Overview

The AsyncRoomManager is an async implementation designed for Phase 2 migration. It manages game rooms asynchronously, preparing for future database integration while maintaining compatibility with the current system.

### Core Responsibilities

1. **Room Lifecycle**: Create, retrieve, and delete rooms asynchronously
2. **Unique ID Generation**: Generate unique 6-character room IDs
3. **Lock Management**: Thread-safe operations with async locks
4. **Statistics Tracking**: Monitor room operations and active games
5. **Empty Room Cleanup**: Remove rooms with no human players
6. **Migration Support**: Sync wrappers for compatibility during transition

## Architecture

### Simple Architecture

```mermaid
graph TB
    subgraph "AsyncRoomManager"
        RM[AsyncRoomManager]
        ROOMS[rooms: Dict[str, AsyncRoom]]
        ML[_manager_lock]
        CL[_room_creation_lock]
        STATS[Statistics]
    end

    subgraph "AsyncRoom Layer"
        R1[AsyncRoom 1]
        R2[AsyncRoom 2]
        R3[AsyncRoom N]
    end

    RM --> ROOMS
    ROOMS --> R1
    ROOMS --> R2
    ROOMS --> R3

    RM --> ML
    RM --> CL
    RM --> STATS

    style RM fill:#4CAF50
    style ROOMS fill:#2196F3
```

### Core Implementation

```python
# backend/engine/async_room_manager.py
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
```

## Room Lifecycle

### Room Creation

```python
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
        logger.info(f"Current rooms in manager: {list(self.rooms.keys())}")

        # Future: await self._persist_room_creation(room_id, host_name)

        return room_id
```

### Room Retrieval

```python
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
        logger.debug(f"Found room {room_id} in AsyncRoomManager")
        return room

    logger.warning(
        f"Room {room_id} not found in AsyncRoomManager. Current rooms: {list(self.rooms.keys())}"
    )
    # Future: Check database if not in memory
    # room = await self._fetch_room_from_db(room_id)

    return None
```

### Room Deletion

```python
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
```

### Listing Available Rooms

```python
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
```

### Room ID Generation

```python
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
```

## AsyncRoom Integration

The AsyncRoomManager works with AsyncRoom objects that handle individual room state:

```python
# backend/engine/async_room.py (simplified view)
class AsyncRoom:
    """Represents a single game room."""

    def __init__(self, room_id: str, host_name: str):
        self.room_id = room_id
        self.host = host_name
        self.players = [host_name]
        self.started = False
        self.created_at = datetime.now()
        self._lock = asyncio.Lock()

    async def summary(self) -> Dict:
        """Get room summary for listing."""
        async with self._lock:
            return {
                "room_id": self.room_id,
                "host": self.host,
                "players": len(self.players),
                "max_players": 4,
                "started": self.started,
                "created_at": self.created_at.isoformat()
            }

    async def is_empty(self) -> bool:
        """Check if room has no human players."""
        # Implementation depends on player tracking
        return len(self.players) == 0

    async def cleanup(self):
        """Clean up room resources."""
        # Future: Clean up game state, connections, etc.
        logger.info(f"Cleaning up room {self.room_id}")
```

## Migration Strategy

The AsyncRoomManager includes compatibility wrappers for gradual migration:

### Sync Wrappers

```python
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
```

These wrappers handle the complex case of being called from within an async context (where `asyncio.run()` would fail) by using a thread pool executor.

## Lock Management

The AsyncRoomManager uses two separate locks to prevent deadlocks and optimize performance:

### Lock Strategy

```python
class AsyncRoomManager:
    def __init__(self):
        # Two separate locks to prevent deadlocks
        self._manager_lock = asyncio.Lock()  # For operations that modify rooms dict
        self._room_creation_lock = asyncio.Lock()  # For room ID generation
```

### Lock Usage Patterns

1. **Room Creation**: Uses `_room_creation_lock` first for ID generation, then `_manager_lock` for dict modification
2. **Room Retrieval**: No lock needed (read operation)
3. **Room Deletion**: Uses only `_manager_lock`
4. **Room Listing**: Uses `_manager_lock` briefly to create snapshot, then releases for summary generation

### Empty Room Cleanup

```python
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
```

## Statistics & Monitoring

### Statistics Tracking

```python
async def get_stats(self) -> Dict:
    """Get manager statistics."""
    async with self._manager_lock:
        return {
            **self._stats,
            "active_rooms": len(self.rooms),
            "started_games": sum(1 for r in self.rooms.values() if r.started),
        }

async def get_room_count(self) -> int:
    """Get total number of active rooms."""
    return len(self.rooms)
```

### Monitoring Implementation

The AsyncRoomManager tracks:
- Total rooms created
- Total rooms deleted
- Total operations performed
- Active rooms count
- Started games count

This data can be exposed through monitoring endpoints for observability.

## Code Examples

### Basic Usage

```python
# Creating the manager
manager = AsyncRoomManager()

# Creating a room
room_id = await manager.create_room("Alice")
print(f"Created room: {room_id}")

# Getting a room
room = await manager.get_room(room_id)
if room:
    summary = await room.summary()
    print(f"Room summary: {summary}")

# Listing available rooms
available = await manager.list_rooms()
print(f"Available rooms: {len(available)}")

# Deleting a room
deleted = await manager.delete_room(room_id)
print(f"Room deleted: {deleted}")

# Get statistics
stats = await manager.get_stats()
print(f"Manager stats: {stats}")
```

### Using Sync Wrappers

```python
# For migration compatibility
room_id = manager.create_room_sync("Bob")
room = manager.get_room_sync(room_id)
rooms = manager.list_rooms_sync()
deleted = manager.delete_room_sync(room_id)
```

### Integration with WebSocket Layer

The AsyncRoomManager is designed to work with the WebSocket layer, but the actual connection management and player tracking is handled by the WebSocket handler and Game State Machine:

```python
# Example integration pattern (not in AsyncRoomManager)
# The actual room joining, player management, and game integration
# is handled by the WebSocket handler and RoomManager (not AsyncRoomManager)

# AsyncRoomManager focuses on:
# - Room lifecycle (create, get, delete, list)
# - Unique ID generation
# - Statistics tracking
# - Migration compatibility

# It does NOT handle:
# - WebSocket connections
# - Player tracking
# - Game state management
# - Broadcasting
# - Bot management
```

## Testing & Debugging

### Unit Testing

```python
@pytest.mark.asyncio
async def test_room_creation():
    """Test room creation flow."""
    manager = AsyncRoomManager()

    # Create room
    room_id = await manager.create_room("Alice")

    # Verify room
    assert room_id is not None
    assert len(room_id) == 6  # Default room ID length
    assert room_id.isupper()

    # Get room
    room = await manager.get_room(room_id)
    assert room is not None
    assert room.host == "Alice"
    assert room.room_id == room_id

    # Check stats
    stats = await manager.get_stats()
    assert stats["rooms_created"] == 1
    assert stats["active_rooms"] == 1
```

### Testing Empty Room Cleanup

```python
@pytest.mark.asyncio
async def test_empty_room_cleanup():
    """Test cleanup of empty rooms."""
    manager = AsyncRoomManager()

    # Create multiple rooms
    room_ids = []
    for i in range(3):
        room_id = await manager.create_room(f"Host{i}")
        room_ids.append(room_id)

    # Mock some rooms as empty
    # (In real implementation, this would be based on player count)

    # Run cleanup
    cleaned = await manager.cleanup_empty_rooms()

    # Verify cleanup
    remaining = await manager.get_room_count()
    assert remaining == 3 - cleaned
```

### Migration Testing

```python
def test_sync_wrappers():
    """Test sync wrapper compatibility."""
    manager = AsyncRoomManager()

    # Test sync creation
    room_id = manager.create_room_sync("TestHost")
    assert room_id is not None

    # Test sync retrieval
    room = manager.get_room_sync(room_id)
    assert room is not None
    assert room.host == "TestHost"

    # Test sync deletion
    deleted = manager.delete_room_sync(room_id)
    assert deleted is True

    # Verify deletion
    room = manager.get_room_sync(room_id)
    assert room is None
```

## Summary

The AsyncRoomManager provides:

1. **Async Room Management**: Complete async lifecycle for room operations
2. **Unique ID Generation**: Generates unique 6-character room IDs
3. **Thread-Safe Operations**: Dual-lock system prevents deadlocks
4. **Migration Support**: Sync wrappers for gradual migration
5. **Future Database Ready**: Prepared for database persistence

Key differences from sync RoomManager:
- Focuses on room lifecycle only (no player/connection management)
- All operations are async with future database hooks
- Simplified architecture without complex subsystems
- Migration-friendly with sync wrapper methods
