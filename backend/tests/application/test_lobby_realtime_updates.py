"""
Tests for lobby real-time updates functionality.

This module tests the real-time synchronization of room states
in the lobby, including room creation, player count updates,
and room state changes.
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime
import asyncio

from application.use_cases.lobby.get_room_list import GetRoomListUseCase
from application.use_cases.room_management.create_room import CreateRoomUseCase
from application.use_cases.room_management.join_room import JoinRoomUseCase
from application.use_cases.room_management.leave_room import LeaveRoomUseCase
from application.dto.lobby import GetRoomListRequest, GetRoomListResponse, RoomSummary
from application.dto.room_management import (
    CreateRoomRequest, CreateRoomResponse,
    JoinRoomRequest, JoinRoomResponse,
    LeaveRoomRequest, LeaveRoomResponse
)
from application.dto.common import RoomInfo, PlayerInfo, PlayerStatus, RoomStatus
from domain.entities.room import Room
from domain.entities.player import Player
from domain.events.room_events import RoomCreated, PlayerJoinedRoom, PlayerLeftRoom
from infrastructure.events.event_broadcast_mapper import event_broadcast_mapper
from unittest.mock import patch


@pytest.fixture
def mock_dependencies():
    """Create mock dependencies for use cases."""
    mock_uow = Mock()
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=None)
    mock_uow.rooms = Mock()
    mock_uow.rooms.find_by_player = AsyncMock(return_value=None)  # Add this mock
    
    mock_event_publisher = Mock()
    mock_event_publisher.publish = AsyncMock()
    
    mock_metrics = Mock()
    mock_metrics.increment = Mock()
    
    # Mock broadcast function
    mock_broadcast = AsyncMock()
    
    return mock_uow, mock_event_publisher, mock_metrics, mock_broadcast


@pytest.fixture
def sample_rooms():
    """Create sample rooms for testing."""
    room1 = Room(room_id="ROOM001", host_name="Alice")
    room2 = Room(room_id="ROOM002", host_name="Bob")
    room3 = Room(room_id="ROOM003", host_name="Charlie")
    
    # Room 2 has 3 players (almost full)
    room2.add_player("Eve", is_bot=False, slot=1)
    room2.add_player("Frank", is_bot=False, slot=2)
    
    return [room1, room2, room3]


class TestRoomCreationVisibility:
    """Test that new rooms appear in lobby immediately after creation."""
    
    @pytest.mark.asyncio
    async def test_newly_created_room_appears_in_lobby(self, mock_dependencies):
        """Test that a newly created room appears in the room list."""
        mock_uow, mock_event_publisher, mock_metrics, _ = mock_dependencies
        
        # Initial state: no rooms
        mock_uow.rooms.list_active = AsyncMock(return_value=[])
        
        # Mock PropertyMapper to return expected values
        with patch('application.use_cases.lobby.get_room_list.PropertyMapper') as mock_mapper:
            mock_mapper.map_room_for_use_case.return_value = {
                'code': 'NEWROOM',
                'name': "Alice's Room",
                'player_count': 4,
                'settings': {'is_private': False},
                'created_at': datetime.utcnow()
            }
            mock_mapper.get_room_attr.return_value = False
            
            # Create room list use case
            get_room_list_use_case = GetRoomListUseCase(mock_uow, mock_metrics)
            
            # Initial request - should return empty list
            request = GetRoomListRequest(player_id="player1", include_full=True)
            response = await get_room_list_use_case.execute(request)
            
            assert len(response.rooms) == 0
            
            # Create a new room
            new_room = Room(room_id="NEWROOM", host_name="Alice")
            
            # Update mock to return the new room
            mock_uow.rooms.list_active = AsyncMock(return_value=[new_room])
            
            # Request room list again (include full rooms since Room creates with 4 slots filled)
            response = await get_room_list_use_case.execute(request)
            
            # Verify new room appears
            assert len(response.rooms) == 1
            assert response.rooms[0].room_id == "NEWROOM"
            assert response.rooms[0].host_name == "Alice"
            assert response.rooms[0].player_count == 4  # Host + 3 bots
    
    @pytest.mark.asyncio
    async def test_multiple_lobby_users_see_new_rooms(self, mock_dependencies):
        """Test that all lobby users see newly created rooms."""
        mock_uow, mock_event_publisher, mock_metrics, mock_broadcast = mock_dependencies
        
        # Setup initial empty state
        mock_uow.rooms.list_active = AsyncMock(return_value=[])
        
        # Simulate multiple users in lobby
        lobby_users = ["user1", "user2", "user3"]
        
        # Create a new room
        new_room = Room(room_id="MULTI001", host_name="Host")
        mock_uow.rooms.list_active = AsyncMock(return_value=[new_room])
        
        # Each user requests room list
        get_room_list_use_case = GetRoomListUseCase(mock_uow, mock_metrics)
        
        for user_id in lobby_users:
            request = GetRoomListRequest(player_id=user_id)
            response = await get_room_list_use_case.execute(request)
            
            # All users should see the new room
            assert len(response.rooms) == 1
            assert response.rooms[0].room_id == "MULTI001"
    
    @pytest.mark.asyncio
    async def test_room_creation_event_broadcast(self, mock_dependencies):
        """Test that room creation triggers proper event broadcast."""
        mock_uow, mock_event_publisher, mock_metrics, _ = mock_dependencies
        
        # Create a room
        room = Room(room_id="EVENT001", host_name="EventHost")
        
        # Emit room created event
        event = RoomCreated(
            room_id="EVENT001",
            host_name="EventHost",
            total_slots=4
        )
        
        # Get broadcast mapping
        broadcast_info = event_broadcast_mapper.map_event(event, None)
        
        assert broadcast_info is not None
        assert broadcast_info["event_name"] == "room_created"
        assert broadcast_info["target_type"] == "response"


class TestPlayerCountUpdates:
    """Test player count updates in real-time."""
    
    @pytest.mark.asyncio
    async def test_player_count_increases_on_join(self, mock_dependencies, sample_rooms):
        """Test that player count increases when someone joins."""
        mock_uow, mock_event_publisher, mock_metrics, _ = mock_dependencies
        
        room = sample_rooms[0]  # Room with just host
        initial_player_count = len([s for s in room.slots if s])
        
        # Add a player
        room.add_player("NewPlayer", is_bot=False, slot=1)
        
        # Setup mock
        mock_uow.rooms.list_active = AsyncMock(return_value=[room])
        
        # Get room list
        get_room_list_use_case = GetRoomListUseCase(mock_uow, mock_metrics)
        request = GetRoomListRequest(player_id="observer")
        response = await get_room_list_use_case.execute(request)
        
        # Verify player count increased
        assert response.rooms[0].player_count == initial_player_count + 1
    
    @pytest.mark.asyncio
    async def test_player_count_decreases_on_leave(self, mock_dependencies, sample_rooms):
        """Test that player count decreases when someone leaves."""
        mock_uow, mock_event_publisher, mock_metrics, _ = mock_dependencies
        
        room = sample_rooms[1]  # Room with multiple players
        initial_player_count = len([s for s in room.slots if s])
        
        # Remove a player
        room.remove_player("Eve")
        
        # Setup mock
        mock_uow.rooms.list_active = AsyncMock(return_value=[room])
        
        # Get room list
        get_room_list_use_case = GetRoomListUseCase(mock_uow, mock_metrics)
        request = GetRoomListRequest(player_id="observer")
        response = await get_room_list_use_case.execute(request)
        
        # Verify player count decreased
        assert response.rooms[0].player_count == initial_player_count - 1
    
    @pytest.mark.asyncio
    async def test_concurrent_player_updates(self, mock_dependencies):
        """Test handling of concurrent player join/leave operations."""
        mock_uow, mock_event_publisher, mock_metrics, _ = mock_dependencies
        
        # Create a room
        room = Room(room_id="CONCURRENT", host_name="Host")
        
        # Simulate concurrent operations
        async def join_player(name: str, slot: int):
            await asyncio.sleep(0.01)  # Simulate network delay
            room.add_player(name, is_bot=False, slot=slot)
        
        async def leave_player(name: str):
            await asyncio.sleep(0.01)  # Simulate network delay
            room.remove_player(name)
        
        # Run concurrent operations
        tasks = [
            join_player("Player1", 1),
            join_player("Player2", 2),
            leave_player("Bot 4"),  # Remove initial bot
        ]
        
        await asyncio.gather(*tasks)
        
        # Verify final state
        player_count = len([s for s in room.slots if s])
        assert player_count == 4  # Host + Player1 + Player2 + remaining bot


class TestRoomStateChanges:
    """Test lobby updates for room state changes."""
    
    @pytest.mark.asyncio
    async def test_room_status_changes_reflected_in_lobby(self, mock_dependencies):
        """Test that room status changes are reflected in lobby."""
        mock_uow, mock_event_publisher, mock_metrics, _ = mock_dependencies
        
        # Create room in WAITING state
        room = Room(room_id="STATUS001", host_name="StatusHost")
        assert room.status == RoomStatus.WAITING
        
        # Setup mock
        mock_uow.rooms.list_active = AsyncMock(return_value=[room])
        
        # Get initial state
        get_room_list_use_case = GetRoomListUseCase(mock_uow, mock_metrics)
        request = GetRoomListRequest(player_id="observer")
        response = await get_room_list_use_case.execute(request)
        
        assert len(response.rooms) == 1
        assert not response.rooms[0].game_in_progress
        
        # Start game (changes status)
        room.start_game()
        
        # Get updated state
        response = await get_room_list_use_case.execute(request)
        
        assert response.rooms[0].game_in_progress
    
    @pytest.mark.asyncio
    async def test_full_room_filtering(self, mock_dependencies, sample_rooms):
        """Test filtering of full rooms from lobby."""
        mock_uow, mock_event_publisher, mock_metrics, _ = mock_dependencies
        
        # Make room 2 full
        room2 = sample_rooms[1]
        room2.add_player("LastPlayer", is_bot=False, slot=3)
        assert room2.is_full()
        
        # Setup mock with all rooms
        mock_uow.rooms.list_active = AsyncMock(return_value=sample_rooms)
        
        # Request without full rooms
        get_room_list_use_case = GetRoomListUseCase(mock_uow, mock_metrics)
        request = GetRoomListRequest(
            player_id="observer",
            include_full=False
        )
        response = await get_room_list_use_case.execute(request)
        
        # Should not include the full room
        room_ids = [r.room_id for r in response.rooms]
        assert "ROOM002" not in room_ids
        
        # Request with full rooms
        request.include_full = True
        response = await get_room_list_use_case.execute(request)
        
        # Should include the full room
        room_ids = [r.room_id for r in response.rooms]
        assert "ROOM002" in room_ids
    
    @pytest.mark.asyncio
    async def test_room_removal_from_lobby(self, mock_dependencies, sample_rooms):
        """Test that deleted rooms are removed from lobby."""
        mock_uow, mock_event_publisher, mock_metrics, _ = mock_dependencies
        
        # Initial state with 3 rooms
        mock_uow.rooms.list_active = AsyncMock(return_value=sample_rooms)
        
        get_room_list_use_case = GetRoomListUseCase(mock_uow, mock_metrics)
        request = GetRoomListRequest(player_id="observer")
        response = await get_room_list_use_case.execute(request)
        
        assert len(response.rooms) == 3
        
        # Remove room 2
        remaining_rooms = [sample_rooms[0], sample_rooms[2]]
        mock_uow.rooms.list_active = AsyncMock(return_value=remaining_rooms)
        
        # Get updated list
        response = await get_room_list_use_case.execute(request)
        
        assert len(response.rooms) == 2
        room_ids = [r.room_id for r in response.rooms]
        assert "ROOM002" not in room_ids


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.mark.asyncio
    async def test_network_delay_simulation(self, mock_dependencies):
        """Test handling of network delays in updates."""
        mock_uow, mock_event_publisher, mock_metrics, _ = mock_dependencies
        
        # Simulate delayed room list retrieval
        async def delayed_list_active(limit=100):
            await asyncio.sleep(0.1)  # 100ms delay
            return [Room(room_id="DELAYED", host_name="DelayedHost")]
        
        mock_uow.rooms.list_active = delayed_list_active
        
        get_room_list_use_case = GetRoomListUseCase(mock_uow, mock_metrics)
        request = GetRoomListRequest(player_id="observer")
        
        # Should still complete successfully
        response = await get_room_list_use_case.execute(request)
        assert len(response.rooms) == 1
    
    @pytest.mark.asyncio
    async def test_empty_lobby_handling(self, mock_dependencies):
        """Test proper handling of empty lobby."""
        mock_uow, mock_event_publisher, mock_metrics, _ = mock_dependencies
        
        # No rooms
        mock_uow.rooms.list_active = AsyncMock(return_value=[])
        
        get_room_list_use_case = GetRoomListUseCase(mock_uow, mock_metrics)
        request = GetRoomListRequest(player_id="lonely_user")
        response = await get_room_list_use_case.execute(request)
        
        assert response.rooms == []
        assert response.total_items == 0
    
    @pytest.mark.asyncio
    async def test_pagination_with_many_rooms(self, mock_dependencies):
        """Test pagination when many rooms exist."""
        mock_uow, mock_event_publisher, mock_metrics, _ = mock_dependencies
        
        # Create many rooms
        many_rooms = [
            Room(room_id=f"ROOM{i:03d}", host_name=f"Host{i}")
            for i in range(25)
        ]
        
        mock_uow.rooms.list_active = AsyncMock(return_value=many_rooms)
        
        get_room_list_use_case = GetRoomListUseCase(mock_uow, mock_metrics)
        
        # First page
        request = GetRoomListRequest(
            player_id="observer",
            page=1,
            page_size=10
        )
        response = await get_room_list_use_case.execute(request)
        
        assert len(response.rooms) == 10
        assert response.total_items == 25
        assert response.page == 1
        
        # Second page
        request.page = 2
        response = await get_room_list_use_case.execute(request)
        
        assert len(response.rooms) == 10
        assert response.page == 2
        
        # Last page
        request.page = 3
        response = await get_room_list_use_case.execute(request)
        
        assert len(response.rooms) == 5  # Remaining rooms
        assert response.page == 3