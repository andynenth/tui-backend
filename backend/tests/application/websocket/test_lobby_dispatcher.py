"""
Tests for lobby-specific WebSocket dispatcher functionality.

This module tests the dispatcher's handling of lobby events
and ensures proper event naming and data formatting.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from application.websocket.use_case_dispatcher import UseCaseDispatcher, DispatchContext
from application.dto.lobby import GetRoomListResponse, RoomSummary
from application.dto.common import RoomInfo, PlayerInfo, PlayerStatus, RoomStatus
from application.exceptions import ValidationException


@pytest.fixture
def mock_dependencies():
    """Create mock dependencies for dispatcher."""
    mock_uow = Mock()
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=None)
    
    return mock_uow


@pytest.fixture
def dispatcher(mock_dependencies):
    """Create dispatcher with mocked dependencies."""
    return UseCaseDispatcher(unit_of_work=mock_dependencies)


@pytest.fixture
def mock_context():
    """Create mock dispatch context."""
    mock_ws = Mock()
    return DispatchContext(
        websocket=mock_ws,
        room_id="lobby",
        player_id="test_player",
        player_name="TestPlayer"
    )


class TestLobbyDispatcherEvents:
    """Test lobby-specific event handling in dispatcher."""
    
    @pytest.mark.asyncio
    async def test_get_rooms_returns_room_list_update_event(
        self, dispatcher, mock_context
    ):
        """Test that get_rooms returns room_list_update event."""
        # Mock the use case response
        mock_rooms = [
            RoomSummary(
                room_id="ROOM001",
                room_code="ROOM001",
                room_name="Test Room 1",
                host_name="Host1",
                player_count=2,
                max_players=4,
                game_in_progress=False,
                is_private=False,
                created_at=datetime.utcnow()
            ),
            RoomSummary(
                room_id="ROOM002",
                room_code="ROOM002",
                room_name="Test Room 2",
                host_name="Host2",
                player_count=3,
                max_players=4,
                game_in_progress=True,
                is_private=False,
                created_at=datetime.utcnow()
            )
        ]
        
        mock_response = GetRoomListResponse(
            rooms=mock_rooms,
            player_current_room=None,
            page=1,
            page_size=20,
            total_items=2
        )
        
        dispatcher.get_room_list_use_case.execute = AsyncMock(
            return_value=mock_response
        )
        
        # Dispatch get_rooms event
        response = await dispatcher.dispatch(
            "get_rooms",
            {},
            mock_context
        )
        
        # Verify response structure
        assert response["event"] == "room_list_update"
        assert "rooms" in response["data"]
        assert "total_count" in response["data"]
        assert len(response["data"]["rooms"]) == 2
        
        # Verify room data
        room1 = response["data"]["rooms"][0]
        assert room1["room_id"] == "ROOM001"
        assert room1["room_name"] == "Test Room 1"
        assert room1["player_count"] == 2
        assert room1["game_in_progress"] is False
        
        room2 = response["data"]["rooms"][1]
        assert room2["room_id"] == "ROOM002"
        assert room2["game_in_progress"] is True
    
    @pytest.mark.asyncio
    async def test_request_room_list_alias(self, dispatcher, mock_context):
        """Test that request_room_list works the same as get_rooms."""
        # Mock the use case
        mock_response = GetRoomListResponse(
            rooms=[],
            player_current_room=None,
            page=1,
            page_size=20,
            total_items=0
        )
        
        dispatcher.get_room_list_use_case.execute = AsyncMock(
            return_value=mock_response
        )
        
        # Test both event names
        response1 = await dispatcher.dispatch(
            "get_rooms",
            {},
            mock_context
        )
        
        response2 = await dispatcher.dispatch(
            "request_room_list",
            {},
            mock_context
        )
        
        # Both should return same event type
        assert response1["event"] == "room_list_update"
        assert response2["event"] == "room_list_update"
    
    @pytest.mark.asyncio
    async def test_room_list_with_filters(self, dispatcher, mock_context):
        """Test room list request with filters."""
        # Mock response
        mock_response = GetRoomListResponse(
            rooms=[],
            player_current_room=None,
            page=2,
            page_size=10,
            total_items=25
        )
        
        dispatcher.get_room_list_use_case.execute = AsyncMock(
            return_value=mock_response
        )
        
        # Request with filters
        response = await dispatcher.dispatch(
            "get_rooms",
            {
                "include_private": True,
                "include_full": True,
                "include_in_game": False,
                "page": 2,
                "page_size": 10
            },
            mock_context
        )
        
        # Verify use case was called with correct parameters
        call_args = dispatcher.get_room_list_use_case.execute.call_args[0][0]
        assert call_args.include_private is True
        assert call_args.include_full is True
        assert call_args.include_in_game is False
        assert call_args.page == 2
        assert call_args.page_size == 10
    
    @pytest.mark.asyncio
    async def test_room_creation_event_format(self, dispatcher, mock_context):
        """Test room creation returns proper event format."""
        # Mock create room response
        mock_room_info = RoomInfo(
            room_id="NEWROOM",
            room_code="NEWROOM",
            room_name="New Room",
            host_id="host_id",
            status=RoomStatus.WAITING,
            players=[
                PlayerInfo(
                    player_id="host_id",
                    player_name="TestPlayer",
                    is_bot=False,
                    is_host=True,
                    status=PlayerStatus.CONNECTED,
                    seat_position=0,
                    score=0,
                    games_played=0,
                    games_won=0
                )
            ],
            max_players=4,
            created_at=datetime.utcnow(),
            game_in_progress=False,
            current_game_id=None
        )
        
        # Mock the create room use case
        mock_create_response = Mock()
        mock_create_response.success = True
        mock_create_response.room_info = mock_room_info
        mock_create_response.join_code = "NEWROOM"
        
        dispatcher.create_room_use_case.execute = AsyncMock(
            return_value=mock_create_response
        )
        
        # Dispatch create room
        response = await dispatcher.dispatch(
            "create_room",
            {"player_name": "TestPlayer"},
            mock_context
        )
        
        # Verify response format
        assert response["event"] == "room_created"
        assert response["data"]["success"] is True
        assert response["data"]["room_id"] == "NEWROOM"
        assert response["data"]["room_code"] == "NEWROOM"
        assert response["data"]["host_name"] == "TestPlayer"
        assert "room_info" in response["data"]
    
    @pytest.mark.asyncio
    async def test_empty_lobby_response(self, dispatcher, mock_context):
        """Test proper response when no rooms exist."""
        # Mock empty response
        mock_response = GetRoomListResponse(
            rooms=[],
            player_current_room=None,
            page=1,
            page_size=20,
            total_items=0
        )
        
        dispatcher.get_room_list_use_case.execute = AsyncMock(
            return_value=mock_response
        )
        
        response = await dispatcher.dispatch(
            "get_rooms",
            {},
            mock_context
        )
        
        assert response["event"] == "room_list_update"
        assert response["data"]["rooms"] == []
        assert response["data"]["total_count"] == 0
    
    @pytest.mark.asyncio
    async def test_player_current_room_included(self, dispatcher, mock_context):
        """Test that player's current room is included if they're in one."""
        # Mock response with current room
        current_room = RoomSummary(
            room_id="CURRENT",
            room_code="CURRENT",
            room_name="My Current Room",
            host_name="Me",
            player_count=3,
            max_players=4,
            game_in_progress=False,
            is_private=False,
            created_at=datetime.utcnow()
        )
        
        mock_response = GetRoomListResponse(
            rooms=[current_room],
            player_current_room=current_room,
            page=1,
            page_size=20,
            total_items=1
        )
        
        dispatcher.get_room_list_use_case.execute = AsyncMock(
            return_value=mock_response
        )
        
        response = await dispatcher.dispatch(
            "get_rooms",
            {},
            mock_context
        )
        
        # Current room should be in the list
        assert len(response["data"]["rooms"]) == 1
        assert response["data"]["rooms"][0]["room_id"] == "CURRENT"
    
    @pytest.mark.asyncio
    async def test_error_handling_for_invalid_filters(
        self, dispatcher, mock_context
    ):
        """Test error handling for invalid filter parameters."""
        # Mock validation error
        dispatcher.get_room_list_use_case.execute = AsyncMock(
            side_effect=ValidationException({"page": "Page must be positive"})
        )
        
        response = await dispatcher.dispatch(
            "get_rooms",
            {"page": -1},
            mock_context
        )
        
        assert response["event"] == "error"
        assert "Failed to handle get_rooms" in response["data"]["message"]
    
    @pytest.mark.asyncio
    async def test_sorting_parameters_passed_correctly(
        self, dispatcher, mock_context
    ):
        """Test that sorting parameters are passed to use case."""
        mock_response = GetRoomListResponse(
            rooms=[],
            player_current_room=None,
            page=1,
            page_size=20,
            total_items=0
        )
        
        dispatcher.get_room_list_use_case.execute = AsyncMock(
            return_value=mock_response
        )
        
        # Request with sorting
        await dispatcher.dispatch(
            "get_rooms",
            {
                "sort_by": "player_count",
                "sort_order": "desc"
            },
            mock_context
        )
        
        # Verify parameters passed
        call_args = dispatcher.get_room_list_use_case.execute.call_args[0][0]
        assert call_args.sort_by == "player_count"
        assert call_args.sort_order == "desc"