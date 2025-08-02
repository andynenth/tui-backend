# backend/tests/test_async_room_manager.py
"""
Tests for AsyncRoomManager and AsyncRoom implementations.
"""

import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from backend.engine.async_room_manager import AsyncRoomManager, RoomCreationResult
from backend.engine.async_room import AsyncRoom
from backend.engine.player import Player


class TestAsyncRoomManager:
    """Test suite for AsyncRoomManager."""
    
    @pytest.mark.asyncio
    async def test_create_room(self):
        """Test async room creation."""
        manager = AsyncRoomManager()
        
        # Create room
        room_id = await manager.create_room("TestHost")
        
        # Verify room was created
        assert room_id is not None
        assert len(room_id) == 6
        assert room_id.isupper()
        
        # Verify room exists
        room = await manager.get_room(room_id)
        assert room is not None
        assert isinstance(room, AsyncRoom)
        assert room.host_name == "TestHost"
        
        # Verify stats
        stats = await manager.get_stats()
        assert stats["rooms_created"] == 1
        assert stats["active_rooms"] == 1
    
    @pytest.mark.asyncio
    async def test_get_room(self):
        """Test async room retrieval."""
        manager = AsyncRoomManager()
        
        # Test non-existent room
        room = await manager.get_room("NONEXISTENT")
        assert room is None
        
        # Create and retrieve room
        room_id = await manager.create_room("TestHost")
        room = await manager.get_room(room_id)
        
        assert room is not None
        assert room.room_id == room_id
        assert room.host_name == "TestHost"
    
    @pytest.mark.asyncio
    async def test_delete_room(self):
        """Test async room deletion."""
        manager = AsyncRoomManager()
        
        # Create room
        room_id = await manager.create_room("TestHost")
        
        # Delete room
        deleted = await manager.delete_room(room_id)
        assert deleted == True
        
        # Verify room is gone
        room = await manager.get_room(room_id)
        assert room is None
        
        # Verify stats
        stats = await manager.get_stats()
        assert stats["rooms_deleted"] == 1
        
        # Test deleting non-existent room
        deleted = await manager.delete_room("NONEXISTENT")
        assert deleted == False
    
    @pytest.mark.asyncio
    async def test_list_rooms(self):
        """Test async room listing."""
        manager = AsyncRoomManager()
        
        # Initially empty
        rooms = await manager.list_rooms()
        assert len(rooms) == 0
        
        # Create some rooms
        room1_id = await manager.create_room("Host1")
        room2_id = await manager.create_room("Host2")
        room3_id = await manager.create_room("Host3")
        
        # Start one game
        room3 = await manager.get_room(room3_id)
        room3.started = True
        
        # List available rooms (excludes started games)
        rooms = await manager.list_rooms()
        assert len(rooms) == 2
        
        # Verify room data
        room_ids = {r["room_id"] for r in rooms}
        assert room1_id in room_ids
        assert room2_id in room_ids
        assert room3_id not in room_ids  # Started game not listed
    
    @pytest.mark.asyncio
    async def test_unique_room_ids(self):
        """Test that room IDs are unique."""
        manager = AsyncRoomManager()
        
        # Create many rooms
        room_ids = set()
        for i in range(100):
            room_id = await manager.create_room(f"Host{i}")
            room_ids.add(room_id)
        
        # All IDs should be unique
        assert len(room_ids) == 100
    
    @pytest.mark.asyncio
    async def test_cleanup_empty_rooms(self):
        """Test cleaning up empty rooms."""
        manager = AsyncRoomManager()
        
        # Create rooms
        room1_id = await manager.create_room("Host1")
        room2_id = await manager.create_room("Host2")
        
        # Make room1 empty (all bots)
        room1 = await manager.get_room(room1_id)
        for i in range(4):
            room1.players[i] = Player(f"Bot{i}", is_bot=True)
        
        # Clean up empty rooms
        cleaned = await manager.cleanup_empty_rooms()
        assert cleaned == 1
        
        # Verify room1 is gone, room2 remains
        assert await manager.get_room(room1_id) is None
        assert await manager.get_room(room2_id) is not None
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test concurrent room operations."""
        manager = AsyncRoomManager()
        
        # Create many rooms concurrently
        async def create_room_task(i):
            return await manager.create_room(f"Host{i}")
        
        room_ids = await asyncio.gather(
            *[create_room_task(i) for i in range(20)]
        )
        
        # All should succeed
        assert len(room_ids) == 20
        assert len(set(room_ids)) == 20  # All unique
        
        # Verify all rooms exist
        for room_id in room_ids:
            room = await manager.get_room(room_id)
            assert room is not None
    
    @pytest.mark.asyncio
    async def test_sync_compatibility_methods(self):
        """Test sync wrapper methods for migration."""
        manager = AsyncRoomManager()
        
        # Test sync wrappers
        room_id = manager.create_room_sync("SyncHost")
        assert room_id is not None
        
        room = manager.get_room_sync(room_id)
        assert room is not None
        assert room.host_name == "SyncHost"
        
        rooms = manager.list_rooms_sync()
        assert len(rooms) == 1
        
        deleted = manager.delete_room_sync(room_id)
        assert deleted == True


class TestAsyncRoom:
    """Test suite for AsyncRoom."""
    
    @pytest.mark.asyncio
    async def test_room_initialization(self):
        """Test async room initialization."""
        room = AsyncRoom("TEST123", "TestHost")
        
        assert room.room_id == "TEST123"
        assert room.host_name == "TestHost"
        assert room.started == False
        assert room.game is None
        
        # Check initial players
        assert room.players[0] is not None
        assert room.players[0].name == "TestHost"
        assert room.players[0].is_bot == False
        
        # Check bot slots
        for i in range(1, 4):
            assert room.players[i] is not None
            assert room.players[i].is_bot == True
    
    @pytest.mark.asyncio
    async def test_join_room(self):
        """Test async player joining."""
        room = AsyncRoom("TEST123", "TestHost")
        
        # Join empty slot
        slot = await room.join_room("Player1")
        assert slot == 1
        assert room.players[1].name == "Player1"
        assert room.players[1].is_bot == False
        
        # Join replaces bot
        slot = await room.join_room("Player2")
        assert slot == 2
        assert room.players[2].name == "Player2"
        
        # Fill last slot
        slot = await room.join_room("Player3")
        assert slot == 3
        
        # Room full - should fail
        with pytest.raises(ValueError) as exc_info:
            await room.join_room("Player4")
        assert "No available slot" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_exit_room(self):
        """Test async player exit."""
        room = AsyncRoom("TEST123", "TestHost")
        
        # Add players
        await room.join_room("Player1")
        await room.join_room("Player2")
        
        # Regular player exit
        is_host = await room.exit_room("Player1")
        assert is_host == False
        assert room.players[1] is None
        
        # Host exit
        is_host = await room.exit_room("TestHost")
        assert is_host == True
        
        # Exit non-existent player
        is_host = await room.exit_room("NonExistent")
        assert is_host == False
    
    @pytest.mark.asyncio
    async def test_assign_slot(self):
        """Test async slot assignment."""
        room = AsyncRoom("TEST123", "TestHost")
        
        # Assign human player
        await room.assign_slot(2, "NewPlayer")
        assert room.players[2].name == "NewPlayer"
        assert room.players[2].is_bot == False
        
        # Assign bot
        await room.assign_slot(3, "BOT_Custom")
        assert room.players[3].name == "BOT_Custom"
        assert room.players[3].is_bot == True
        
        # Clear slot
        await room.assign_slot(2, None)
        assert room.players[2] is None
        
        # Invalid slot
        with pytest.raises(ValueError):
            await room.assign_slot(5, "Player")
    
    @pytest.mark.asyncio
    async def test_start_game(self):
        """Test async game start."""
        room = AsyncRoom("TEST123", "TestHost")
        
        # Mock broadcast callback
        broadcast_callback = AsyncMock()
        
        # Fill all slots
        await room.join_room("Player1")
        await room.join_room("Player2")
        await room.join_room("Player3")
        
        # Mock bot manager
        with patch('backend.engine.bot_manager.BotManager') as mock_bot_manager:
            mock_bot_manager.return_value.register_game = MagicMock()
            
            # Start game
            result = await room.start_game(broadcast_callback)
            
            assert result["success"] == True
            assert room.started == True
            assert room.game is not None
            assert room.game_state_machine is not None
            
            # Verify bot manager called
            mock_bot_manager.return_value.register_game.assert_called_once()
        
        # Can't start again
        with pytest.raises(ValueError) as exc_info:
            await room.start_game(broadcast_callback)
        assert "Game already started" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_room_summary(self):
        """Test async room summary generation."""
        room = AsyncRoom("TEST123", "TestHost")
        
        # Add some players
        await room.join_room("Player1")
        
        # Get summary
        summary = await room.summary()
        
        assert summary["room_id"] == "TEST123"
        assert summary["host_name"] == "TestHost"
        assert summary["started"] == False
        assert summary["occupied_slots"] == 4
        assert summary["total_slots"] == 4
        
        # Check slots
        assert summary["slots"]["P1"]["name"] == "TestHost"
        assert summary["slots"]["P1"]["is_host"] == True
        assert summary["slots"]["P2"]["name"] == "Player1"
        assert summary["slots"]["P2"]["is_host"] == False
    
    @pytest.mark.asyncio
    async def test_migrate_host(self):
        """Test async host migration."""
        room = AsyncRoom("TEST123", "TestHost")
        
        # Add players
        await room.join_room("Player1")
        await room.join_room("Player2")
        
        # Migrate to human player
        new_host = await room.migrate_host()
        assert new_host == "Player1"
        assert room.host_name == "Player1"
        
        # Migrate again - should find next human who isn't current host
        new_host = await room.migrate_host()
        # Should be either TestHost or Player2 (whoever isn't the current host)
        assert new_host in ["TestHost", "Player2"]
        assert room.host_name == new_host
        
        # Clear all humans except current host
        for i, player in enumerate(room.players):
            if player and not player.is_bot and player.name != room.host_name:
                room.players[i] = None
        
        # Should migrate to bot
        new_host = await room.migrate_host()
        assert new_host == "Bot 4"
        assert room.host_name == "Bot 4"
    
    @pytest.mark.asyncio
    async def test_concurrent_joins(self):
        """Test concurrent join operations."""
        room = AsyncRoom("TEST123", "TestHost")
        
        # Try to join 10 players concurrently
        async def try_join(i):
            try:
                slot = await room.join_room(f"Player{i}")
                return (i, slot, None)
            except ValueError as e:
                return (i, None, str(e))
        
        results = await asyncio.gather(
            *[try_join(i) for i in range(10)]
        )
        
        # Only 3 should succeed (slots 1-3)
        successful = [(i, slot) for i, slot, err in results if err is None]
        failed = [(i, err) for i, slot, err in results if err is not None]
        
        assert len(successful) == 3
        assert len(failed) == 7
        
        # Check all got different slots
        slots = [slot for _, slot in successful]
        assert len(set(slots)) == 3
    
    @pytest.mark.asyncio
    async def test_room_activity_tracking(self):
        """Test room activity tracking."""
        room = AsyncRoom("TEST123", "TestHost")
        
        # Check initial timestamps
        assert room._created_at is not None
        assert room._last_activity is not None
        
        # Activity should update on operations
        initial_activity = room._last_activity
        await asyncio.sleep(0.1)
        
        await room.join_room("Player1")
        assert room._last_activity > initial_activity
        
        # Check stats
        assert room._total_joins == 1
        assert room._total_exits == 0
        
        await room.exit_room("Player1")
        assert room._total_exits == 1