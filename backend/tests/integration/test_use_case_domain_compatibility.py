#!/usr/bin/env python3
"""
Integration tests to verify use cases work with actual domain entities.
This prevents AttributeError bugs from mismatched expectations.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock

# Domain entities
from domain.entities.room import Room
from domain.entities.player import Player

# Use cases to test
from application.use_cases.room_management.get_room_state import GetRoomStateUseCase
from application.use_cases.room_management.create_room import CreateRoomUseCase
from application.dto.room_management import GetRoomStateRequest, CreateRoomRequest


class TestDomainCompatibility:
    """Test that use cases work with actual domain entities."""
    
    @pytest.fixture
    def mock_uow(self):
        """Create a mock unit of work."""
        uow = AsyncMock()
        uow.rooms = AsyncMock()
        uow.rooms.get = AsyncMock()
        uow.rooms.save = AsyncMock()
        uow.rooms.get_by_code = AsyncMock(return_value=None)
        uow.rooms.find_by_player = AsyncMock(return_value=None)
        return uow
    
    @pytest.fixture
    def mock_event_publisher(self):
        """Create a mock event publisher."""
        publisher = AsyncMock()
        publisher.publish = AsyncMock()
        return publisher
    
    @pytest.fixture
    def sample_room(self):
        """Create a real Room entity with actual properties."""
        room = Room(
            room_id="TEST123",
            host_name="TestHost",
            max_slots=4
        )
        # Room.__post_init__ automatically adds host + 3 bots
        return room
    
    @pytest.mark.asyncio
    async def test_get_room_state_with_real_room(self, mock_uow, sample_room):
        """Test that GetRoomStateUseCase works with actual Room entity."""
        # Setup
        mock_uow.rooms.get.return_value = sample_room
        use_case = GetRoomStateUseCase(mock_uow, None)
        
        # Create request
        request = GetRoomStateRequest(
            room_id="TEST123",
            requesting_player_id="player123",
            include_game_state=False
        )
        
        # Execute - this should NOT raise AttributeError
        try:
            response = await use_case.execute(request)
            
            # Verify response
            assert response.success is True
            assert response.room_info.room_id == "TEST123"
            assert len(response.room_info.players) == 4  # Host + 3 bots
            assert response.room_info.players[0].player_name == "TestHost"
            assert response.room_info.players[0].is_host is True
            assert response.room_info.players[1].is_bot is True
            
            print("✅ GetRoomStateUseCase works with real Room entity")
            
        except AttributeError as e:
            pytest.fail(f"AttributeError in use case: {e}")
    
    @pytest.mark.asyncio
    async def test_create_room_generates_proper_response(self, mock_uow, mock_event_publisher):
        """Test that CreateRoomUseCase generates proper response."""
        # Setup
        use_case = CreateRoomUseCase(mock_uow, mock_event_publisher, None)
        
        # Create request
        request = CreateRoomRequest(
            host_player_id="player123",
            host_player_name="TestPlayer",
            room_name="Test Room",
            max_players=4,
            win_condition_type="score",
            win_condition_value=50,
            allow_bots=True,
            is_private=False
        )
        
        # Execute
        try:
            response = await use_case.execute(request)
            
            # Verify the saved room has correct properties
            save_calls = mock_uow.rooms.save.call_args_list
            assert len(save_calls) == 1
            saved_room = save_calls[0][0][0]  # First positional argument
            
            # Check that the room has expected properties
            assert hasattr(saved_room, 'room_id')
            assert hasattr(saved_room, 'host_name')
            assert hasattr(saved_room, 'slots')
            assert hasattr(saved_room, 'game')
            assert not hasattr(saved_room, 'id')  # Should NOT have 'id'
            assert not hasattr(saved_room, 'current_game')  # Should NOT have 'current_game'
            
            print("✅ CreateRoomUseCase creates room with correct properties")
            
        except AttributeError as e:
            pytest.fail(f"AttributeError in use case: {e}")
    
    def test_room_entity_properties(self, sample_room):
        """Document actual Room entity properties."""
        print("\n📋 Actual Room Entity Properties:")
        print(f"  - room_id: {sample_room.room_id}")
        print(f"  - host_name: {sample_room.host_name}")
        print(f"  - max_slots: {sample_room.max_slots}")
        print(f"  - slots: {len(sample_room.slots)} slots")
        print(f"  - status: {sample_room.status}")
        print(f"  - game: {sample_room.game}")
        
        # What it does NOT have
        assert not hasattr(sample_room, 'id')
        assert not hasattr(sample_room, 'host_id')
        assert not hasattr(sample_room, 'current_game')
        assert not hasattr(sample_room, 'settings')
        assert not hasattr(sample_room, 'code')
        assert not hasattr(sample_room, 'created_at')
        
        print("\n❌ Properties Room does NOT have:")
        print("  - id, host_id, current_game, settings, code, created_at")
    
    def test_player_entity_properties(self, sample_room):
        """Document actual Player entity properties."""
        player = sample_room.slots[0]  # Get the host player
        
        print("\n📋 Actual Player Entity Properties:")
        print(f"  - name: {player.name}")
        print(f"  - is_bot: {player.is_bot}")
        print(f"  - score: {player.score}")
        print(f"  - hand: {len(player.hand)} pieces")
        
        # What it does NOT have
        assert not hasattr(player, 'id')
        assert not hasattr(player, 'player_id')
        assert not hasattr(player, 'games_played')
        assert not hasattr(player, 'games_won')
        
        print("\n❌ Properties Player does NOT have:")
        print("  - id, player_id, games_played, games_won")


if __name__ == "__main__":
    # Run tests
    test = TestDomainCompatibility()
    
    # Create fixtures
    room = test.sample_room()
    
    # Run property tests
    test.test_room_entity_properties(room)
    test.test_player_entity_properties(room)
    
    # Run async tests
    async def run_async_tests():
        uow = test.mock_uow()
        publisher = test.mock_event_publisher()
        
        await test.test_get_room_state_with_real_room(uow, room)
        await test.test_create_room_generates_proper_response(uow, publisher)
    
    asyncio.run(run_async_tests())
    
    print("\n✅ All tests passed!")