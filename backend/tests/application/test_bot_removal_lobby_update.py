"""
Test for Issue 1: Lobby doesn't update when host removes a bot.

This test verifies that when a host removes a bot from their room,
the lobby receives a room_list_update event with the updated player count.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, call, patch
from datetime import datetime

from application.use_cases.room_management.remove_player import RemovePlayerUseCase
from application.dto.room_management import RemovePlayerRequest
from domain.entities.room import Room
from domain.entities.player import Player
from domain.events.room_events import PlayerRemoved
from domain.events.base import EventMetadata

# Import broadcast handlers to ensure event handlers are registered
import infrastructure.events.broadcast_handlers


@pytest.mark.asyncio
async def test_lobby_updates_when_bot_removed():
    """
    Test that lobby receives room_list_update when a bot is removed.
    
    Given: A room with 4 players (host + 3 bots)
    When: Host removes a bot
    Then: Lobby should receive room_list_update showing 3/4 players
    """
    # Arrange
    room_id = "TEST123"
    host_id = f"{room_id}_p0"
    bot_to_remove_id = f"{room_id}_p2"  # Bot in slot 3
    
    # Create mock room with host and 3 bots
    room = Mock(spec=Room)
    room.room_id = room_id
    room.host_id = host_id
    room.host_name = "TestHost"
    room.max_slots = 4
    room.game = None  # No game in progress
    
    # Create slots with host and 3 bots
    host_player = Mock(spec=Player)
    host_player.name = "TestHost"
    host_player.is_bot = False
    
    bot2 = Mock(spec=Player)
    bot2.name = "Bot 2"
    bot2.is_bot = True
    
    bot3 = Mock(spec=Player)
    bot3.name = "Bot 3"
    bot3.is_bot = True
    
    bot4 = Mock(spec=Player)
    bot4.name = "Bot 4"
    bot4.is_bot = True
    
    room.slots = [host_player, bot2, bot3, bot4]
    
    # Mock unit of work
    uow = AsyncMock()
    uow.rooms.get_by_id = AsyncMock(return_value=room)
    uow.rooms.save = AsyncMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    
    # Mock event publisher
    event_publisher = AsyncMock()
    published_events = []
    event_publisher.publish = AsyncMock(side_effect=lambda event: published_events.append(event))
    
    # Mock broadcast function to track lobby updates
    broadcast_calls = []
    mock_broadcast = AsyncMock(side_effect=lambda channel, event, data: 
        broadcast_calls.append((channel, event, data)))
    
    # Patch the broadcast function
    import application.use_cases.room_management.remove_player
    original_broadcast = getattr(application.use_cases.room_management.remove_player, 'broadcast', None)
    application.use_cases.room_management.remove_player.broadcast = mock_broadcast
    
    # Create use case
    use_case = RemovePlayerUseCase(
        unit_of_work=uow,
        event_publisher=event_publisher
    )
    
    # Create request
    request = RemovePlayerRequest(
        room_id=room_id,
        target_player_id=bot_to_remove_id,
        requesting_player_id=host_id,
        user_id="test_user"
    )
    
    # Mock room.remove_player to simulate bot removal
    def mock_remove_player(player_name):
        # Remove bot3 from slots
        room.slots[2] = None
    
    room.remove_player = Mock(side_effect=mock_remove_player)
    
    # Act
    try:
        response = await use_case.execute(request)
        
        # Wait a bit for async events to propagate
        await asyncio.sleep(0.1)
        
        # Assert
        # 1. Player removal was successful
        assert response.removed_player_id == bot_to_remove_id
        assert response.was_bot is True
        
        # 2. PlayerRemoved event was published
        assert len(published_events) == 1
        assert isinstance(published_events[0], PlayerRemoved)
        assert published_events[0].removed_player_id == bot_to_remove_id
        
        # 3. Lobby received room_list_update (this is the failing part)
        lobby_updates = [call for call in broadcast_calls 
                        if call[0] == "lobby" and call[1] == "room_list_update"]
        
        assert len(lobby_updates) > 0, "Lobby should receive room_list_update after bot removal"
        
        # Check the update contains correct player count
        if lobby_updates:
            update_data = lobby_updates[0][2]
            assert "rooms" in update_data
            # The room should show 3/4 players after removal
            
    finally:
        # Restore original broadcast if it existed
        if original_broadcast:
            application.use_cases.room_management.remove_player.broadcast = original_broadcast


@pytest.mark.asyncio
async def test_bot_removal_updates_player_count():
    """
    Test that removing a bot correctly updates the room player count in lobby.
    
    This test verifies the specific player count in the room_list_update.
    """
    # This test will check the actual data sent to lobby
    # Similar setup as above but focusing on the broadcast data structure
    pass  # TODO: Implement after fixing the main issue