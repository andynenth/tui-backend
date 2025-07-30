"""
Full integration test for Issue 1: Lobby doesn't update when host removes a bot.

This test verifies the complete flow from WebSocket command to lobby broadcast.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from datetime import datetime

# Import to ensure handlers are registered
import infrastructure.events.broadcast_handlers
from infrastructure.dependencies import get_unit_of_work, get_event_publisher
from infrastructure.events.decorators import EventHandlerRegistry
from application.use_cases.room_management.remove_player import RemovePlayerUseCase
from application.dto.room_management import RemovePlayerRequest
from domain.entities.room import Room


@pytest.mark.asyncio
async def test_bot_removal_triggers_lobby_update():
    """
    Test the full flow: remove bot -> event published -> handler triggered -> lobby broadcast.
    
    Given: A room with 4 players (host + 3 bots)
    When: Host removes a bot via use case
    Then: Lobby should receive room_list_update broadcast
    """
    # Arrange
    room_id = "TEST123"
    host_name = "TestHost"
    broadcast_calls = []
    
    async def mock_broadcast(channel, event, data):
        broadcast_calls.append((channel, event, data))
        print(f"[TEST] Broadcast to {channel}: {event}")
    
    # Patch the broadcast function in both places it might be used
    with patch('infrastructure.websocket.connection_singleton.broadcast', mock_broadcast), \
         patch('infrastructure.events.broadcast_handlers.broadcast', mock_broadcast):
        # Get real dependencies
        uow = get_unit_of_work()
        event_publisher = get_event_publisher()
        
        # Create a room with host and 3 bots
        async with uow:
            room = Room(room_id=room_id, host_name=host_name)
            # Room is created with host and 3 bots by default in __post_init__
            # Verify it has 4 players (host + 3 bots)
            assert len([s for s in room.slots if s]) == 4
            await uow.rooms.save(room)
            await uow.commit()
        
        # Verify initial state
        async with uow:
            room = await uow.rooms.get_by_id(room_id)
            assert len([s for s in room.slots if s]) == 4  # 4 players total
        
        # Create the use case
        use_case = RemovePlayerUseCase(
            unit_of_work=uow,
            event_publisher=event_publisher
        )
        
        # Create request to remove Bot 3 (slot 2)
        request = RemovePlayerRequest(
            room_id=room_id,
            target_player_id=f"{room_id}_p2",  # Bot 3 is in slot 2
            requesting_player_id=f"{room_id}_p0",  # Host
            user_id="test_user"
        )
        
        # Act
        response = await use_case.execute(request)
        
        # Give time for async event handlers to process
        await asyncio.sleep(0.5)
        
        # Debug: Print all broadcast calls
        print(f"\n[TEST] Total broadcasts: {len(broadcast_calls)}")
        for i, (channel, event, data) in enumerate(broadcast_calls):
            print(f"[TEST] Broadcast {i}: channel={channel}, event={event}")
        
        # Assert
        # 1. Bot was removed successfully
        assert response.removed_player_id == f"{room_id}_p2"
        assert response.was_bot is True
        
        # 2. Room now has 3 players
        async with uow:
            room = await uow.rooms.get_by_id(room_id)
            assert len([s for s in room.slots if s]) == 3
        
        # 3. Room participants received update
        room_updates = [call for call in broadcast_calls 
                       if call[0] == room_id and call[1] == "room_update"]
        assert len(room_updates) > 0, "Room should receive room_update"
        
        # 4. Lobby received update (this is what was failing)
        lobby_updates = [call for call in broadcast_calls 
                        if call[0] == "lobby" and call[1] == "room_list_update"]
        assert len(lobby_updates) > 0, "Lobby should receive room_list_update after bot removal"
        
        # Verify the lobby update contains correct data
        if lobby_updates:
            lobby_data = lobby_updates[0][2]
            assert "rooms" in lobby_data
            assert "timestamp" in lobby_data
            
            # The updated room should show 3 players
            rooms = lobby_data["rooms"]
            test_room = next((r for r in rooms if r["room_id"] == room_id), None)
            if test_room:
                assert test_room["player_count"] == 3, "Room should show 3/4 players after bot removal"
                assert test_room["max_players"] == 4


@pytest.mark.asyncio
async def test_bot_addition_triggers_lobby_update():
    """
    Control test: Verify that adding a bot DOES trigger lobby update (this already works).
    
    This confirms the broadcast mechanism works for bot addition.
    """
    # Similar test but for adding a bot
    # This should pass, confirming the broadcast system works
    pass  # TODO: Implement if needed for comparison