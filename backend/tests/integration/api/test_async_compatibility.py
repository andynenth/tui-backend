# backend/tests/test_async_compatibility.py
"""
Tests for async compatibility layer.
Demonstrates gradual migration from sync to async.
"""

import asyncio
import pytest
from unittest.mock import MagicMock, patch

from engine.room import Room
from engine.room_manager import RoomManager
from engine.async_compat import (
    AsyncCompatRoom,
    AsyncCompatRoomManager,
    run_sync_in_async,
    create_async_method,
    ensure_async_room,
)
from tests.async_test_utils import (
    AsyncTestHelper,
    async_test,
    AsyncMockFactory,
    AsyncAssertions,
)


class TestAsyncCompatibilityLayer:
    """Test suite for async compatibility layer."""

    @pytest.mark.asyncio
    async def test_room_manager_async_wrapper(self):
        """Test AsyncCompatRoomManager wraps sync RoomManager correctly."""
        # Create sync room manager
        sync_manager = RoomManager()

        # Wrap in async compatibility layer
        async_manager = AsyncCompatRoomManager(sync_manager)

        # Test create_room
        room_id = await async_manager.create_room("TestHost")
        assert room_id is not None
        assert len(room_id) == 6

        # Verify room was created in sync manager
        sync_room = sync_manager.get_room(room_id)
        assert sync_room is not None
        assert sync_room.host_name == "TestHost"

        # Test get_room returns AsyncCompatRoom
        async_room = await async_manager.get_room(room_id)
        assert async_room is not None
        assert isinstance(async_room, AsyncCompatRoom)
        assert async_room.host_name == "TestHost"

        # Test delete_room
        await async_manager.delete_room(room_id)
        assert sync_manager.get_room(room_id) is None

    @pytest.mark.asyncio
    async def test_room_async_wrapper(self):
        """Test AsyncCompatRoom wraps sync Room correctly."""
        # Create sync room
        sync_room = Room("TEST123", "TestHost")

        # Wrap in async compatibility layer
        async_room = AsyncCompatRoom(sync_room)

        # Test property access
        assert async_room.room_id == "TEST123"
        assert async_room.host_name == "TestHost"
        assert async_room.started == False

        # Test join_room
        slot = await async_room.join_room("Player1")
        assert slot == 1  # Second slot (host is in first)

        # Verify player was added to sync room
        assert sync_room.players[1] is not None
        assert sync_room.players[1].name == "Player1"

        # Test assign_slot
        await async_room.assign_slot(2, "Player2")
        assert sync_room.players[2] is not None
        assert sync_room.players[2].name == "Player2"

        # Test exit_room
        is_host = await async_room.exit_room("Player1")
        assert is_host == False
        assert sync_room.players[1] is None

    @pytest.mark.asyncio
    async def test_concurrent_room_operations(self):
        """Test concurrent operations are properly synchronized."""
        sync_manager = RoomManager()
        async_manager = AsyncCompatRoomManager(sync_manager)

        # Create a room
        room_id = await async_manager.create_room("TestHost")
        room = await async_manager.get_room(room_id)

        # Define concurrent join operations
        async def join_player(player_name):
            try:
                slot = await room.join_room(player_name)
                return (player_name, slot, None)
            except Exception as e:
                return (player_name, None, str(e))

        # Run 10 concurrent join attempts (but room only has 4 slots)
        helper = AsyncTestHelper()
        results = await helper.run_concurrent_operations(
            *[lambda i=i: join_player(f"Player{i}") for i in range(10)]
        )

        # Count successful joins
        successful_joins = [(name, slot) for name, slot, err in results if err is None]
        failed_joins = [(name, err) for name, slot, err in results if err is not None]

        # Should have exactly 3 successful joins (1 host + 3 players)
        assert len(successful_joins) == 3
        assert len(failed_joins) == 7

        # Verify all successful joins got unique slots
        slots = [slot for _, slot in successful_joins]
        assert len(set(slots)) == 3

        # Verify error messages for failed joins
        for _, err in failed_joins:
            assert "No available slot" in err

    @pytest.mark.asyncio
    async def test_sync_compatibility_methods(self):
        """Test sync compatibility methods for gradual migration."""
        sync_manager = RoomManager()
        async_manager = AsyncCompatRoomManager(sync_manager)

        # Test sync wrapper methods
        # These allow old sync code to call new async implementation
        room_id = async_manager.create_room_sync("SyncHost")
        assert room_id is not None

        room = async_manager.get_room_sync(room_id)
        assert room is not None
        assert room.host_name == "SyncHost"

    @pytest.mark.asyncio
    async def test_decorator_utilities(self):
        """Test async utility decorators."""

        # Test run_sync_in_async decorator
        @run_sync_in_async
        def sync_function(x, y):
            return x + y

        result = await sync_function(5, 3)
        assert result == 8

        # Test create_async_method
        class TestClass:
            def __init__(self):
                self.value = 10

            def sync_method(self, x):
                return self.value * x

        TestClass.async_method = create_async_method(TestClass.sync_method)

        obj = TestClass()
        result = await obj.async_method(5)
        assert result == 50

    @pytest.mark.asyncio
    async def test_ensure_async_room(self):
        """Test ensure_async_room utility."""
        # Test with sync room
        sync_room = Room("TEST", "Host")
        async_room = ensure_async_room(sync_room)
        assert isinstance(async_room, AsyncCompatRoom)
        assert async_room.room_id == "TEST"

        # Test with already async room (should return as-is)
        async_room2 = ensure_async_room(async_room)
        assert async_room2 is async_room

    @pytest.mark.asyncio
    async def test_async_locks_prevent_race_conditions(self):
        """Test that async locks properly prevent race conditions."""
        sync_room = Room("TEST", "Host")
        async_room = AsyncCompatRoom(sync_room)

        # Track join order
        join_order = []

        async def join_with_delay(player_name, delay):
            await asyncio.sleep(delay)
            slot = await async_room.join_room(player_name)
            join_order.append((player_name, slot))
            return slot

        # Start joins with different delays
        # Without locks, these might interfere with each other
        tasks = [
            join_with_delay("Player1", 0.01),
            join_with_delay("Player2", 0.005),
            join_with_delay("Player3", 0.002),
        ]

        results = await asyncio.gather(*tasks)

        # All should succeed with different slots
        assert len(set(results)) == 3
        assert all(isinstance(r, int) for r in results)

        # Verify join order matches slot assignment
        # (not necessarily matching delay order due to locks)
        assert len(join_order) == 3

    @pytest.mark.asyncio
    async def test_error_propagation(self):
        """Test that errors properly propagate through async wrapper."""
        sync_room = Room("TEST", "Host")
        async_room = AsyncCompatRoom(sync_room)

        # Fill all slots
        await async_room.join_room("Player1")
        await async_room.join_room("Player2")
        await async_room.join_room("Player3")

        # Next join should fail
        with pytest.raises(ValueError) as exc_info:
            await async_room.join_room("Player4")

        assert "No available slot" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_websocket_integration_pattern(self):
        """Test pattern for WebSocket handler integration."""
        # Simulate WebSocket handler using async room manager
        sync_manager = RoomManager()
        async_manager = AsyncCompatRoomManager(sync_manager)

        # Mock WebSocket handler pattern
        async def websocket_handler(room_id: str, player_name: str):
            # Get room (async)
            room = await async_manager.get_room(room_id)
            if not room:
                return {"error": "Room not found"}

            # Join room (async)
            try:
                slot = await room.join_room(player_name)
                return {"success": True, "slot": slot}
            except ValueError as e:
                return {"error": str(e)}

        # Create room
        room_id = await async_manager.create_room("Host")

        # Test WebSocket handler
        result = await websocket_handler(room_id, "Player1")
        assert result["success"] == True
        assert result["slot"] == 1

        # Test error case
        result = await websocket_handler("INVALID", "Player2")
        assert result["error"] == "Room not found"


class TestMigrationPattern:
    """Test patterns for migrating from sync to async."""

    @pytest.mark.asyncio
    async def test_gradual_migration_pattern(self):
        """Demonstrate gradual migration pattern."""

        # Step 1: Original sync code
        sync_manager = RoomManager()
        room_id = sync_manager.create_room("Host")
        sync_room = sync_manager.get_room(room_id)

        # Step 2: Wrap in async compatibility
        async_manager = AsyncCompatRoomManager(sync_manager)

        # Step 3: New async code can work with wrapped objects
        async_room = await async_manager.get_room(room_id)
        assert async_room is not None

        # Step 4: Async operations work on same underlying data
        await async_room.join_room("AsyncPlayer")

        # Step 5: Sync code still sees the changes
        assert sync_room.players[1] is not None
        assert sync_room.players[1].name == "AsyncPlayer"

        # Step 6: Both sync and async can coexist during migration
        sync_room.join_room("SyncPlayer")  # Sync call
        await async_room.join_room("AsyncPlayer2")  # Async call

        # Verify both worked
        assert sync_room.players[2].name == "SyncPlayer"
        assert sync_room.players[3].name == "AsyncPlayer2"
