"""
Simple test to verify the lobby event name fix.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from application.websocket.use_case_dispatcher import UseCaseDispatcher, DispatchContext
from application.dto.lobby import GetRoomListResponse, RoomSummary
from datetime import datetime


@pytest.mark.asyncio
async def test_get_rooms_returns_room_list_update_event():
    """Test that get_rooms returns room_list_update event (not room_list)."""
    # Create mock UoW
    mock_uow = Mock()
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=None)
    
    # Create dispatcher
    dispatcher = UseCaseDispatcher(unit_of_work=mock_uow)
    
    # Mock the use case response
    mock_rooms = [
        RoomSummary(
            room_id="ROOM001",
            room_code="ROOM001", 
            room_name="Test Room",
            host_name="TestHost",
            player_count=2,
            max_players=4,
            game_in_progress=False,
            is_private=False,
            created_at=datetime.utcnow()
        )
    ]
    
    mock_response = GetRoomListResponse(
        rooms=mock_rooms,
        player_current_room=None,
        page=1,
        page_size=20,
        total_items=1
    )
    
    # Mock the execute method
    dispatcher.get_room_list_use_case.execute = AsyncMock(return_value=mock_response)
    
    # Create context
    mock_ws = Mock()
    context = DispatchContext(
        websocket=mock_ws,
        room_id="lobby",
        player_id="test_player",
        player_name="TestPlayer"
    )
    
    # Dispatch get_rooms event
    response = await dispatcher.dispatch("get_rooms", {}, context)
    
    # VERIFY THE FIX: Event should be "room_list_update" not "room_list"
    assert response["event"] == "room_list_update"
    assert "rooms" in response["data"]
    assert len(response["data"]["rooms"]) == 1
    assert response["data"]["rooms"][0]["room_id"] == "ROOM001"
    
    print("✅ SUCCESS: get_rooms returns 'room_list_update' event")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_get_rooms_returns_room_list_update_event())